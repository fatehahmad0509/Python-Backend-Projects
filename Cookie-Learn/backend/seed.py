
# Database seeding: populates languages, curriculum content, achievements, and demo accounts
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from models import Achievement, Language, Lesson, Question, Section, Unit, User
from security import hash_password


LANGUAGES = [
    ("en", "English", "English", "🇬🇧", 0),
    ("tr", "Turkish", "Turkish", "🇹🇷", 1),
    ("az", "Azerbaijani", "Azərbaycanca", "🇦🇿", 2),
    ("de", "German", "Deutsch", "🇩🇪", 3),
    ("fr", "French", "Français", "🇫🇷", 4),
    ("es", "Spanish", "Español", "🇪🇸", 5),
    ("it", "Italian", "Italiano", "🇮🇹", 6),
    ("ja", "Japanese", "日本語", "🇯🇵", 7),
    ("ko", "Korean", "한국어", "🇰🇷", 8),
    ("ru", "Russian", "Русский", "🇷🇺", 9),
]

ACHIEVEMENTS = [
    ("first_lesson", "First Step", "Complete your first lesson", "Sparkles", "#F59E0B", "lessons", 1, 20),
    ("ten_lessons", "Determined", "Complete 10 lessons", "BookOpen", "#8B5CF6", "lessons", 10, 60),
    ("fifty_lessons", "Student", "Complete 50 lessons", "GraduationCap", "#3B82F6", "lessons", 50, 200),
    ("streak_3", "On Fire", "3-day streak", "Flame", "#EF4444", "streak", 3, 30),
    ("streak_7", "Weekly Hero", "7-day streak", "Flame", "#F97316", "streak", 7, 80),
    ("streak_30", "Legendary", "30-day streak", "Flame", "#DC2626", "streak", 30, 300),
    ("xp_100", "Beginner", "Earn 100 XP", "Zap", "#8B5CF6", "xp", 100, 25),
    ("xp_1000", "Wise", "Earn 1000 XP", "Zap", "#A78BFA", "xp", 1000, 150),
    ("xp_5000", "Master", "Earn 5000 XP", "Crown", "#F59E0B", "xp", 5000, 500),
    ("perfect_5", "Perfectionist", "5 perfect lessons", "Star", "#10B981", "perfect_lessons", 5, 100),
    ("words_100", "Word Hunter", "Learn 100 words", "Book", "#3B82F6", "words", 100, 80),
    ("words_500", "Dictionary", "Learn 500 words", "Book", "#2563EB", "words", 500, 250),
]


def _mc(prompt: str, prompt_tr: str, options: list[str], correct: str, explanation: str) -> dict:
    # Helper to build a multiple-choice question dict
    return {
        "type": "multiple_choice",
        "prompt": prompt,
        "prompt_translation": prompt_tr,
        "data": {"options": options},
        "correct_answer": correct,
        "explanation": explanation,
    }


def _tr(prompt: str, prompt_tr: str, correct: str, direction: str, explanation: str) -> dict:
    # Helper to build a translation question dict
    return {
        "type": "translation",
        "prompt": prompt,
        "prompt_translation": prompt_tr,
        "data": {"direction": direction},
        "correct_answer": correct,
        "explanation": explanation,
    }


def _wm(pairs: list[dict], explanation: str) -> dict:
    # Helper to build a word-match question dict
    return {
        "type": "word_match",
        "prompt": "Match",
        "prompt_translation": "Match",
        "data": {"pairs": pairs},
        "correct_answer": "matched",
        "explanation": explanation,
    }


# Full English curriculum with units, sections, lessons, and questions
EN_CURRICULUM = [
    {
        "title": "Basic Greetings",
        "cefr": "A1", "color": "#8B5CF6", "icon": "Sparkles",
        "description": "First words and greetings in English",
        "sections": [
            {
                "title": "Hello!",
                "lessons": [
                    {
                        "title": "Greetings",
                        "topic": "greetings",
                        "icon": "Hand",
                        "questions": [
                            _mc("What does 'Hello' mean?", "What does 'Hello' mean?", ["Hello", "Goodbye", "Thanks", "Yes"], "Hello", "'Hello' is a common greeting."),
                            _mc("Choose: 'Good morning'", "Which one means 'Good morning'?", ["Good night", "Good morning", "Good bye", "Good afternoon"], "Good morning", "'Good morning' is used in the morning."),
                            _mc("___ evening!", "Fill in the blank: Good ___ (evening time)", ["Good", "Nice", "Well", "Bad"], "Good", "The evening greeting is 'Good evening'."),
                            _tr("Thank you", "Translate from English", "Thank you", "to_native", "'Thank you' is a common expression of gratitude."),
                            _tr("How are you", "Translate from English", "How are you", "to_native", "'How are you' is a common greeting question."),
                            _wm([
                                {"a": "Hello", "b": "A greeting"},
                                {"a": "Bye", "b": "A farewell"},
                                {"a": "Please", "b": "A polite request"},
                                {"a": "Sorry", "b": "An apology"},
                            ], "Word matches: basic courtesy expressions."),
                        ],
                    },
                    {
                        "title": "Introduce Yourself",
                        "topic": "introductions",
                        "icon": "User",
                        "questions": [
                            _mc("What does 'My name is Ali' mean?", "What is the translation of this sentence?", ["My name is Ali", "I am fine", "What is your name?", "Hello Ali"], "My name is Ali", "'My name is ...' is a self-introduction pattern."),
                            _mc("I ___ from Turkey.", "Fill in: 'I' takes 'am'", ["am", "is", "are", "be"], "am", "'am' is used with 'I'."),
                            _tr("I am a student.", "Translate from English", "I am a student", "to_native", "'I am a student' expresses one's occupation."),
                            _tr("Nice to meet you", "Translate from English", "Nice to meet you", "to_native", "'Nice to meet you' is a standard meeting phrase."),
                            _mc("What's your ___ ?", "How do you ask for someone's name?", ["age", "name", "job", "city"], "name", "'What's your name?' asks for a person's name."),
                            _mc("She ___ from Spain.", "'is/are/am' — third person singular?", ["are", "am", "is", "be"], "is", "'is' is used with third person singular subjects."),
                        ],
                    },
                    {
                        "title": "Numbers 1-10",
                        "topic": "numbers",
                        "icon": "Hash",
                        "questions": [
                            _mc("Which number is 'Three'?", "Find the number", ["2", "3", "4", "5"], "3", "Three is the number 3."),
                            _mc("What is the English word for 5?", "What is the English word for the number 5?", ["Four", "Five", "Six", "Seven"], "Five", "Five is the English word for 5."),
                            _wm([
                                {"a": "One", "b": "Number 1"},
                                {"a": "Two", "b": "Number 2"},
                                {"a": "Three", "b": "Number 3"},
                                {"a": "Four", "b": "Number 4"},
                            ], "Number matching."),
                            _mc("I have ___ apples.", "Number of apples: 7", ["five", "six", "seven", "eight"], "seven", "Seven is the number 7."),
                            _tr("Ten", "Translate from English", "Ten", "to_native", "Ten is the number 10."),
                        ],
                    },
                ],
            },
            {
                "title": "Family & Friends",
                "lessons": [
                    {
                        "title": "Family Members",
                        "topic": "family",
                        "icon": "Users",
                        "questions": [
                            _mc("What does 'Mother' mean?", "Family member", ["Father", "Mother", "Sibling", "Child"], "Mother", "Mother is a female parent."),
                            _mc("What does 'Brother' mean?", "Family member", ["Brother", "Sister", "Uncle", "Father"], "Brother", "Brother is a male sibling."),
                            _wm([
                                {"a": "Father", "b": "Male parent"},
                                {"a": "Mother", "b": "Female parent"},
                                {"a": "Sister", "b": "Female sibling"},
                                {"a": "Brother", "b": "Male sibling"},
                            ], "Family members matching"),
                            _tr("I have two siblings", "Translate from English", "I have two siblings", "to_native", "'Sibling' means a brother or sister."),
                            _mc("My ___ is a teacher.", "Mother is a teacher.", ["mother", "father", "brother", "sister"], "mother", "Mother refers to a female parent."),
                        ],
                    },
                ],
            },
        ],
    },
    {
        "title": "Daily Life",
        "cefr": "A1", "color": "#3B82F6", "icon": "Sun",
        "description": "Food, colors, and daily verbs",
        "sections": [
            {
                "title": "Colors",
                "lessons": [
                    {
                        "title": "Basic Colors",
                        "topic": "colors",
                        "icon": "Palette",
                        "questions": [
                            _mc("What does 'Red' mean?", "Color", ["Red", "Blue", "Green", "Yellow"], "Red", "Red is a primary color."),
                            _mc("What does 'Blue' mean?", "Color", ["Green", "Blue", "Purple", "White"], "Blue", "Blue is a primary color."),
                            _wm([
                                {"a": "Green", "b": "Color of grass"},
                                {"a": "Yellow", "b": "Color of the sun"},
                                {"a": "Black", "b": "Darkest color"},
                                {"a": "White", "b": "Lightest color"},
                            ], "Color matching"),
                            _tr("The sky is blue.", "Translate from English", "The sky is blue", "to_native", "'The sky is blue' describes a common fact."),
                        ],
                    },
                ],
            },
            {
                "title": "Food",
                "lessons": [
                    {
                        "title": "Fruits & Vegetables",
                        "topic": "food",
                        "icon": "Apple",
                        "questions": [
                            _mc("What does 'Apple' mean?", "Fruit", ["Orange", "Apple", "Banana", "Grape"], "Apple", "Apple is a type of fruit."),
                            _mc("What does 'Bread' mean?", "Food", ["Water", "Milk", "Bread", "Cheese"], "Bread", "Bread is a common food item."),
                            _mc("I like ___.", "I like coffee.", ["tea", "coffee", "juice", "milk"], "coffee", "Coffee is a popular drink."),
                            _tr("I am drinking water.", "Translate from English", "I am drinking water", "to_native", "Present continuous: am/is/are + -ing"),
                        ],
                    },
                ],
            },
        ],
    },
    {
        "title": "Personal AI Exercises",
        "cefr": "A2", "color": "#F59E0B", "icon": "Sparkles",
        "description": "Dynamic questions generated instantly by AI",
        "sections": [
            {
                "title": "For Me",
                "lessons": [
                    {"title": "AI Practice - General", "topic": "general", "icon": "Wand", "ai_dynamic": True},
                    {"title": "AI Practice - Grammar", "topic": "grammar", "icon": "PenTool", "ai_dynamic": True},
                    {"title": "AI Practice - Speaking", "topic": "speaking", "icon": "MessageCircle", "ai_dynamic": True},
                ],
            }
        ],
    },
]

# Starter curriculum for non-English languages (AI-generated lessons only)
STARTER_UNITS_OTHER = [
    {
        "title": "Beginner",
        "cefr": "A1", "color": "#8B5CF6", "icon": "Sparkles",
        "description": "First steps",
        "sections": [
            {
                "title": "First Words",
                "lessons": [
                    {"title": "AI Practice - Greetings", "topic": "greetings", "icon": "Hand", "ai_dynamic": True},
                    {"title": "AI Practice - Numbers", "topic": "numbers", "icon": "Hash", "ai_dynamic": True},
                    {"title": "AI Practice - Colors", "topic": "colors", "icon": "Palette", "ai_dynamic": True},
                ],
            }
        ],
    },
    {
        "title": "Daily Life",
        "cefr": "A2", "color": "#3B82F6", "icon": "Sun",
        "description": "Practice for daily conversations",
        "sections": [
            {
                "title": "Speaking Practice",
                "lessons": [
                    {"title": "AI Practice - Family", "topic": "family", "icon": "Users", "ai_dynamic": True},
                    {"title": "AI Practice - Food", "topic": "food", "icon": "Apple", "ai_dynamic": True},
                    {"title": "AI Practice - Free", "topic": "general", "icon": "Wand", "ai_dynamic": True},
                ],
            }
        ],
    },
]


def _seed_curriculum(db: Session, language: Language, unit_defs: list[dict]) -> None:
    # Create units, sections, lessons, and questions for a language from definition dicts
    existing_units = db.query(Unit).filter(Unit.language_id == language.id).count()
    if existing_units > 0:
        return
    for u_idx, u in enumerate(unit_defs):
        unit = Unit(
            language_id=language.id, order_index=u_idx, title=u["title"],
            description=u.get("description"), color=u.get("color", "#8B5CF6"),
            icon=u.get("icon", "Sparkles"), cefr_level=u.get("cefr", "A1"),
        )
        db.add(unit)
        db.flush()
        for s_idx, s in enumerate(u["sections"]):
            section = Section(unit_id=unit.id, order_index=s_idx, title=s["title"])
            db.add(section)
            db.flush()
            for l_idx, l in enumerate(s["lessons"]):
                lesson = Lesson(
                    section_id=section.id, order_index=l_idx, title=l["title"],
                    topic=l.get("topic"), icon=l.get("icon", "BookOpen"),
                    xp_reward=l.get("xp", 15),
                    is_ai_dynamic=l.get("ai_dynamic", False),
                )
                db.add(lesson)
                db.flush()
                for q_idx, q in enumerate(l.get("questions", [])):
                    db.add(Question(
                        lesson_id=lesson.id, order_index=q_idx,
                        type=q["type"], prompt=q["prompt"],
                        prompt_translation=q.get("prompt_translation"),
                        data=q["data"], correct_answer=q["correct_answer"],
                        explanation=q.get("explanation"),
                    ))
    db.commit()


def seed_all() -> None:
    # Main seed function: creates languages, curricula, achievements, admin, and demo user
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for code, name, native, flag, order in LANGUAGES:
            if not db.query(Language).filter(Language.code == code).first():
                db.add(Language(code=code, name=name, native_name=native, flag_emoji=flag, order_index=order))
        db.commit()

        for code, *_ in LANGUAGES:
            lang = db.query(Language).filter(Language.code == code).first()
            if not lang:
                continue
            if code == "en":
                _seed_curriculum(db, lang, EN_CURRICULUM)
            else:
                _seed_curriculum(db, lang, STARTER_UNITS_OTHER)

        for code, title, desc, icon, color, ctype, cval, xp in ACHIEVEMENTS:
            if not db.query(Achievement).filter(Achievement.code == code).first():
                db.add(Achievement(code=code, title=title, description=desc, icon=icon, color=color,
                                    condition_type=ctype, condition_value=cval, xp_reward=xp))
        db.commit()

        admin = db.query(User).filter(User.email == "admin@cookielearn.app").first()
        if not admin:
            admin = User(
                email="admin@cookielearn.app",
                username="admin",
                password_hash=hash_password("admin123"),
                full_name="Cookie Admin",
                is_admin=True,
                native_language_code="en",
                active_language_code="en",
            )
            db.add(admin)
            db.commit()

        demo = db.query(User).filter(User.email == "demo@cookielearn.app").first()
        if not demo:
            demo = User(
                email="demo@cookielearn.app",
                username="demo",
                password_hash=hash_password("demo123"),
                full_name="Demo Learner",
                is_admin=False,
                native_language_code="en",
                active_language_code="en",
                xp_total=120, streak_days=3, longest_streak=5, hearts=5, gems=80,
            )
            db.add(demo)
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
    print("Seed complete.")
