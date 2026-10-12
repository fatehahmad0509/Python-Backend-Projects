
# AI service layer - interfaces with Google Gemini API for chat, quiz generation, evaluation, and translation
import json
import os
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import APIError

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")

_client: genai.Client | None = None


def get_client() -> genai.Client:
    # Lazy-initialized Gemini client singleton
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


LANGUAGE_NAMES = {
    "en": "English",
    "tr": "Turkish",
    "az": "Azerbaijani",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "ru": "Russian",
}


def lang_name(code: str | None) -> str:
    return LANGUAGE_NAMES.get((code or "").lower(), code or "English")


def _generate_text(prompt: str, system: str, temperature: float = 0.6) -> str:
    # Send a prompt and return text response from Gemini
    client = get_client()
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                max_output_tokens=1400,
            ),
        )
        return (response.text or "").strip()
    except APIError as e:
        raise RuntimeError(f"AI service error: {e}")


def _generate_json(prompt: str, system: str, schema: dict | None = None, temperature: float = 0.7) -> Any:
    # Send a prompt and parse the response as JSON
    client = get_client()
    cfg_kwargs: dict[str, Any] = {
        "system_instruction": system,
        "temperature": temperature,
        "response_mime_type": "application/json",
        "max_output_tokens": 4096,
    }
    if schema is not None:
        cfg_kwargs["response_schema"] = schema
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(**cfg_kwargs),
        )
        text = (response.text or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.strip()
        return json.loads(text)
    except APIError as e:
        raise RuntimeError(f"AI service error: {e}")
    except json.JSONDecodeError:
        raise RuntimeError("AI did not return valid JSON")


def chat_teacher(history: list[dict], user_message: str, target_language: str | None, native_language: str = "tr") -> str:
    # Teacher-style chat: Cookie responds in native language with learning tips
    tgt = lang_name(target_language) if target_language else "the target language"
    system = (
        f"You are 'Cookie', a friendly, patient AI language teacher inside CookieLearn — a Duolingo-style app. "
        f"The learner's native language is {lang_name(native_language)} and they are learning {tgt}. "
        f"ALWAYS reply in {lang_name(native_language)} unless the learner explicitly writes in {tgt} or asks for {tgt} content. "
        f"Keep answers short (2-5 sentences), use vivid examples in {tgt} with translations in parentheses. "
        f"Refuse politely if asked about unrelated topics — bring the conversation back to language learning."
    )
    convo_lines = []
    for m in history[-10:]:
        role = "Student" if m["role"] == "user" else "Cookie"
        convo_lines.append(f"{role}: {m['content']}")
    convo_lines.append(f"Student: {user_message}")
    convo_lines.append("Cookie:")
    prompt = "\n".join(convo_lines)
    return _generate_text(prompt, system, temperature=0.7)


def chat_practice(history: list[dict], user_message: str, target_language: str, native_language: str = "tr") -> str:
    # Practice-style chat: AI responds only in target language with optional corrections
    tgt = lang_name(target_language)
    system = (
        f"You are a native speaker of {tgt} chatting casually with a language learner whose native language is {lang_name(native_language)}. "
        f"Respond ONLY in {tgt}, with natural, everyday phrasing. "
        f"If the learner made a grammar or spelling mistake in their last message, add a short section starting with '💡' where you gently correct in {lang_name(native_language)}, "
        f"showing the corrected sentence and a brief tip. Keep replies 1-3 sentences plus the optional correction."
    )
    convo_lines = []
    for m in history[-12:]:
        role = "Learner" if m["role"] == "user" else "You"
        convo_lines.append(f"{role}: {m['content']}")
    convo_lines.append(f"Learner: {user_message}")
    convo_lines.append("You:")
    prompt = "\n".join(convo_lines)
    return _generate_text(prompt, system, temperature=0.8)


def explain_wrong_answer(*, language_code: str, question_type: str, prompt: str, correct_answer: str, user_answer: str, native_language: str = "tr") -> dict:
    # Get AI explanation for why a learner's answer was wrong
    tgt = lang_name(language_code)
    system = (
        f"You are Cookie, a warm language coach. Explain WHY a learner's answer is wrong in {tgt} learning. "
        f"Reply strictly in {lang_name(native_language)} for the 'explanation' and 'correction_hint'. "
        f"Provide 2-3 short example sentences in {tgt} (with parenthetical native translations)."
    )
    user_prompt = (
        f"Question type: {question_type}\nPrompt: {prompt}\n"
        f"Correct answer: {correct_answer}\nLearner's answer: {user_answer}\n\n"
        f"Return JSON with keys: explanation (string), correction_hint (string), examples (array of 2-3 strings)."
    )
    schema = {
        "type": "object",
        "properties": {
            "explanation": {"type": "string"},
            "correction_hint": {"type": "string"},
            "examples": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["explanation", "correction_hint", "examples"],
    }
    return _generate_json(user_prompt, system, schema=schema, temperature=0.4)


def explain_word(*, word: str, language_code: str, native_language: str = "tr") -> dict:
    # Get a comprehensive word explanation from AI
    tgt = lang_name(language_code)
    system = (
        f"You are a dictionary and language coach. Explain a {tgt} word for a learner whose native language is {lang_name(native_language)}."
    )
    prompt = (
        f"Word: {word}\nLanguage: {tgt}\nNative language for explanations: {lang_name(native_language)}.\n\n"
        f"Return JSON with keys: word, meaning (in {lang_name(native_language)}), pronunciation (IPA or simple), "
        f"part_of_speech, synonyms (array of 3), antonyms (array up to 3), examples (array of 3 objects with keys 'sentence' in {tgt} and 'translation' in {lang_name(native_language)}), tips (short usage tip in {lang_name(native_language)})."
    )
    schema = {
        "type": "object",
        "properties": {
            "word": {"type": "string"},
            "meaning": {"type": "string"},
            "pronunciation": {"type": "string"},
            "part_of_speech": {"type": "string"},
            "synonyms": {"type": "array", "items": {"type": "string"}},
            "antonyms": {"type": "array", "items": {"type": "string"}},
            "examples": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"sentence": {"type": "string"}, "translation": {"type": "string"}},
                    "required": ["sentence", "translation"],
                },
            },
            "tips": {"type": "string"},
        },
        "required": ["word", "meaning", "pronunciation", "synonyms", "examples"],
    }
    return _generate_json(prompt, system, schema=schema, temperature=0.4)


ALLOWED_TYPES = ["multiple_choice", "translation", "word_match"]


def generate_quiz(*, language_code: str, level_code: str, topic: str | None, num_questions: int, types_wanted: list[str] | None, native_language: str = "tr", weak_topics: list[str] | None = None) -> dict:
    # Generate a set of quiz questions using AI, targeting the learner's level and weak areas
    tgt = lang_name(language_code)
    types_wanted = [t for t in (types_wanted or []) if t in ALLOWED_TYPES] or ["multiple_choice", "translation", "word_match"]
    weak_hint = ""
    if weak_topics:
        weak_hint = f"The learner has struggled with: {', '.join(weak_topics)}. Include a few questions targeting these."
    system = (
        f"You are a CEFR-aligned {tgt} curriculum designer. Generate exercises for a learner at level {level_code} "
        f"whose native language is {lang_name(native_language)}. All content must be grammatically correct, natural, and pedagogically useful. "
        f"Vary questions each time — never repeat the same sentence. "
        f"CRITICAL RULES: (1) The 'prompt' must NEVER contain or reveal the correct answer. "
        f"(2) The 'prompt_translation' field is ONLY a native-language hint about the task; for TRANSLATION questions leave prompt_translation as null (it would give away the answer). "
        f"(3) Do NOT add meta-text like 'What is the answer?' — the question type already implies that. "
        f"(4) For multiple_choice: the 'prompt' asks a question, and ONE of the options is the correct_answer; the other 3 are plausible distractors."
    )
    prompt = (
        f"Create exactly {num_questions} exercises for {tgt}. Level: {level_code}. "
        f"Topic focus: {topic or 'general'}. {weak_hint} "
        f"Allowed types: {types_wanted}.\n\n"
        f"For each question return an object with keys: type, prompt, prompt_translation (nullable, in {lang_name(native_language)}), data, correct_answer, explanation (in {lang_name(native_language)}).\n"
        f"Data schema per type:\n"
        f"- multiple_choice: prompt is a question (e.g. \"How do you say 'good morning' in {tgt}?\"); data = {{\"options\": [4 strings in {tgt}, one of them is the correct_answer]}}. prompt_translation may be a short native hint but MUST NOT contain the answer verbatim.\n"
        f"- translation: prompt is a sentence in ONE language. data = {{\"direction\": \"to_target\" (prompt is native, answer target) or \"to_native\" (prompt is target, answer native)}}; correct_answer is the translation. prompt_translation MUST BE null for translation questions.\n"
        f"- word_match: data = {{\"pairs\": [{{\"a\": target word, \"b\": native word}}, ... 4 pairs]}}; correct_answer = \"matched\".\n\n"
        f"Return JSON: {{\"questions\": [ ... ]}}."
    )
    result = _generate_json(prompt, system, schema=None, temperature=0.85)
    if isinstance(result, list):
        result = {"questions": result}
    return result


def translate_and_explain(*, text: str, target_language_code: str, source_language_code: str | None, native_language: str = "tr") -> dict:
    # Translate text and provide grammar/usage explanation
    tgt = lang_name(target_language_code)
    src = lang_name(source_language_code) if source_language_code else "auto-detected"
    system = f"You are a translator and grammar coach. Provide translation and pedagogy notes in {lang_name(native_language)}."
    prompt = (
        f"Translate to {tgt}: \"{text}\" (source: {src}). "
        f"Return JSON with keys: translation ({tgt}), explanation (in {lang_name(native_language)}, briefly explain the meaning and usage), "
        f"grammar_notes (in {lang_name(native_language)}, short note about tense/structure)."
    )
    schema = {
        "type": "object",
        "properties": {
            "translation": {"type": "string"},
            "explanation": {"type": "string"},
            "grammar_notes": {"type": "string"},
        },
        "required": ["translation", "explanation"],
    }
    return _generate_json(prompt, system, schema=schema, temperature=0.4)



def evaluate_answer(
    *,
    language_code: str,
    level_code: str,
    question_type: str,
    prompt: str,
    correct_answer: str,
    user_answer: str,
    native_language: str = "tr",
) -> dict:
    # Use AI to leniently evaluate whether a learner's answer is semantically and grammatically acceptable
    tgt = lang_name(language_code)
    nat = lang_name(native_language)
    system = (
        f"You are a LENIENT but accurate {tgt} language grading assistant. "
        f"Your job: decide whether a learner's answer is semantically equivalent AND grammatically acceptable — "
        f"NOT whether it exactly matches the sample answer. "
        f"Accept: minor spelling variants, punctuation/capitalization differences, alternative wordings that preserve meaning, "
        f"regional variants, synonyms. "
        f"Reject: wrong meaning, missing key concept, seriously broken grammar. "
        f"Reply strictly in {nat} for 'feedback'."
    )
    prompt_content = (
        f"Question type: {question_type}\n"
        f"Prompt: {prompt}\n"
        f"Sample correct answer: {correct_answer}\n"
        f"Learner's answer: {user_answer}\n\n"
        f"Return JSON with keys: is_correct (boolean), feedback (in {nat}, 1-2 short sentences explaining why), "
        f"correction (a corrected version in the answer's target language if wrong; otherwise empty string)."
    )
    schema = {
        "type": "object",
        "properties": {
            "is_correct": {"type": "boolean"},
            "feedback": {"type": "string"},
            "correction": {"type": "string"},
        },
        "required": ["is_correct", "feedback"],
    }
    return _generate_json(prompt_content, system, schema=schema, temperature=0.15)
