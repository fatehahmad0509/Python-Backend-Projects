import os
import asyncio
import json
import re
import requests
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
from aiohttp import web

from pdf import create_pdf
from db import setup_db, check_limit, increment_quiz

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_state = {}


async def generate_questions(grade: str, subject: str, topic: str, difficulty: str, count: int) -> list[dict]:
    difficulty_label = {"easy": "easy", "medium": "medium", "hard": "hard"}[difficulty]

    prompt = (
        f'You are a Turkish education expert. Generate EXACTLY {count} multiple-choice questions '
        f'for {grade}th grade {subject} class on the topic "{topic}" at {difficulty_label} difficulty level.\n\n'
        f'IMPORTANT: Questions must ONLY cover the topic "{topic}", do not write questions from other topics.\n'
        f'Questions must ONLY be at the {grade}th grade Turkish MEB curriculum level.\n'
        f'DO NOT use higher-grade topics (inclined plane, contact force, trigonometry, derivatives, integrals, etc.).\n'
        f'Do not use formulas or concepts unknown to a {grade}th grade student.\n'
        f'Difficulty level must be {difficulty_label}:\n'
        '- Easy: Basic definition and rule questions, direct formula application\n'
        '- Medium: Problems requiring multiple steps, combining concepts\n'
        '- Hard: Multi-step proofs and problem solving, questions requiring intuition and deep understanding\n\n'
        'RULES:\n'
        '- Each question must have 4 options (A, B, C, D)\n'
        '- Questions must comply with the Turkish MEB curriculum\n'
        '- Answer choices must be evenly distributed\n'
        '- Write exponents with ^: x^2, 2x^3, 1s^2 etc.\n'
        '- Do not use underscores (_) in questions or options\n'
        '- All questions and options must be in Turkish ONLY, do NOT use English, German, French, Vietnamese or any foreign words\n'
        '- Each question must be DIFFERENT from others, do not repeat the same question\n'
        '- Mathematical values must be realistic and correct, do not ask about impossible scenarios\n'
        '- Write every word that has a Turkish equivalent in Turkish: kenar, uzunluk, açı, alan etc.\n'
        '- Write ONLY questions that exactly match the given grade, subject, topic and difficulty level\n'
        '- Return ONLY JSON, write nothing else\n\n'
        'FORMAT:\n'
        '[\n'
        '  {\n'
        '    "question": "Question text?",\n'
        '    "A": "First option",\n'
        '    "B": "Second option",\n'
        '    "C": "Third option",\n'
        '    "D": "Fourth option",\n'
        '    "answer": "A"\n'
        '  }\n'
        ']'
    )

    def do_single_request(p):
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 8192,
                "messages": [{"role": "user", "content": p}]
            },
            timeout=60
        )
        if not resp.ok:
            raise Exception(f"HTTP {resp.status_code}: {resp.text}")
        text = resp.json()["content"][0]["text"]
        text = re.sub(r"```json|```", "", text).strip()
        return json.loads(text)

    loop = asyncio.get_event_loop()

    BATCH = 20
    if count <= BATCH:
        return await loop.run_in_executor(None, do_single_request, prompt)

    all_questions = []
    remaining = count
    batch_num = 1
    while remaining > 0:
        batch_count = min(BATCH, remaining)
        batch_prompt = prompt.replace(
            f"EXACTLY {count} multiple-choice questions",
            f"EXACTLY {batch_count} DIFFERENT multiple-choice questions"
        ) + f"\n\nNOTE: This is batch {batch_num}, write questions DIFFERENT from previously generated ones."
        batch = await loop.run_in_executor(None, do_single_request, batch_prompt)
        all_questions.extend(batch)
        remaining -= batch_count
        batch_num += 1

    return all_questions


def class_keyboard():
    GRADES = ["5", "6", "7", "8", "9", "10", "11", "12"]
    buttons = []
    row = []
    for i, grade in enumerate(GRADES, 1):
        row.append(InlineKeyboardButton(text=f"Grade {grade}", callback_data=f"class_{grade}"))
        if i % 4 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def difficulty_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Easy 🟢", callback_data="diff_easy"),
        InlineKeyboardButton(text="Medium 🟡", callback_data="diff_medium"),
        InlineKeyboardButton(text="Hard 🔴", callback_data="diff_hard"),
    ]])


@dp.message(Command("start"))
async def start(message: Message):
    uid = message.from_user.id
    await message.answer("⏳ Checking...")
    loop = asyncio.get_event_loop()
    can_use, reason = await loop.run_in_executor(None, check_limit, uid)
    if not can_use:
        if reason == "whitelist":
            await message.answer(
                "❌ You are not authorized to use this bot!\n\n"
                "Visit quizbot.onrender.com to purchase a Teacher Membership!"
            )
        elif reason == "suspended":
            await message.answer("🚫 Your subscription has been cancelled. Please contact us.")
        elif reason == "limit":
            await message.answer(
                "⚠️ You have reached your monthly quiz limit!\n\n"
                "Visit quizbot.onrender.com to upgrade your plan!"
            )
        else:
            await message.answer("⚠️ An error occurred, please try again.")
        return
    user_state.pop(uid, None)
    await message.answer("📚 Welcome to QuizBot!\n\nSelect a grade:", reply_markup=class_keyboard())

@dp.callback_query(F.data.startswith("class_"))
async def select_class(callback: CallbackQuery):
    grade = callback.data.replace("class_", "")
    user_state[callback.from_user.id] = {"class": grade, "step": "subject"}
    await callback.message.answer(
        f"📘 Grade {grade} - Enter the subject name:\n\n<i>Example: Mathematics, Physics, Literature</i>",
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("diff_"))
async def select_diff(callback: CallbackQuery):
    uid = callback.from_user.id
    user_state[uid]["difficulty"] = callback.data.replace("diff_", "")
    user_state[uid]["step"] = "count"
    await callback.message.answer("How many questions? (1-30)")
    await callback.answer()

@dp.message(F.text)
async def handle_text(message: Message):
    uid = message.from_user.id
    if uid not in user_state:
        await message.answer("Type /start to begin.")
        return

    state = user_state[uid]
    step = state.get("step")

    if step == "subject":
        state["subject"] = message.text.strip()
        state["step"] = "school"
        await message.answer("🏫 Enter the school name:\n\n<i>Example: Lincoln High School</i>", parse_mode="HTML")

    elif step == "school":
        state["school"] = message.text.strip()
        state["step"] = "topic"
        await message.answer(
            f"📝 {state['subject']} — Enter the topic name:\n\n<i>Example: Equations, Cell Biology, Ottoman History</i>",
            parse_mode="HTML"
        )

    elif step == "topic":
        state["topic"] = message.text.strip()
        state["step"] = "difficulty"
        await message.answer(f'Select difficulty for topic "{state["topic"]}":', reply_markup=difficulty_keyboard())

    elif step == "count":
        try:
            count = int(message.text.strip())
            if count < 1 or count > 30:
                await message.answer("Please enter a number between 1 and 30.")
                return
        except ValueError:
            await message.answer("Please enter a number 😄")
            return

        grade    = state["class"]
        subject  = state["subject"]
        topic    = state["topic"]
        difficulty = state["difficulty"]
        school   = state.get("school", "")
        difficulty_label = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}[difficulty]

        user_state.pop(uid)

        loop = asyncio.get_event_loop()
        can_use, reason = await loop.run_in_executor(None, check_limit, uid)
        if not can_use:
            if reason == "whitelist":
                await message.answer(
                    "❌ You are not authorized to use this bot!\n\n"
                    "Visit quizbot.onrender.com to purchase a Teacher Membership!"
                )
            elif reason == "suspended":
                await message.answer(
                    "🚫 Your subscription has been cancelled. Please contact us."
                )
            elif reason == "limit":
                await message.answer(
                    "⚠️ You have reached your monthly quiz limit!\n\n"
                    "Visit quizbot.onrender.com to upgrade your plan!"
                )
            else:
                await message.answer("⚠️ An error occurred, please try again.")
            return

        await message.answer(f"⏳ Generating {count} questions for Grade {grade} {subject} — {topic} ({difficulty_label})...")

        try:
            questions = await generate_questions(grade, subject, topic, difficulty, count)
            pdf_file, answers = create_pdf(questions, grade=grade, subject=subject, topic=topic, difficulty=difficulty_label, school=school)
            await message.answer_document(FSInputFile(pdf_file), caption=f"📄 Grade {grade} {subject} — {topic}")
            await message.answer(f"📌 Answer Key:\n{answers}")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, increment_quiz, uid)
        except Exception as e:
            await message.answer(f"⚠️ An error occurred: {e}")


async def handle(request):
    return web.Response(text="QuizBot running 😎")

app = web.Application()
app.router.add_get("/", handle)

async def start_bot():
    print("start_bot() called")
    try:
        print("Connecting to DB...")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, setup_db)
    except Exception as e:
        import traceback
        print(f"DB ERROR: {e}")
        print(traceback.format_exc())
    print("BOT STARTED 😎")
    asyncio.create_task(dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()))

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    async def main():
        await start_bot()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000)))
        await site.start()
        print("WEB SERVER STARTED ✅")
        await asyncio.Event().wait()

    asyncio.run(main())
