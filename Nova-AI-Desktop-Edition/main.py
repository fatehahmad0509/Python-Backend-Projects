import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
from settings import Settings

load_dotenv()

# --- CONFIG ---
config = Settings()
MODEL = config.settings.get("model") or "gemini-3.1-flash-lite"

api_key=config.settings.get("api_key")

if not api_key:
    api_key = None

gemini_client = genai.Client(api_key=api_key)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nova_memory.db")


# --- DB ---

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_message(role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO messages (role, content, timestamp) VALUES (?, ?, ?)",
        (role, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_recent_messages(limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT role, content, timestamp FROM messages ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = c.fetchall()
    conn.close()
    return list(reversed([
        {"role": r[0], "content": r[1], "timestamp": r[2]}
        for r in rows
    ]))


def search_messages(query: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT role, content, timestamp FROM messages WHERE content LIKE ? ORDER BY id DESC LIMIT 15",
        (f"%{query}%",)
    )
    rows = c.fetchall()
    conn.close()
    return [
        {"role": r[0], "content": r[1], "timestamp": r[2]}
        for r in rows
    ]


# --- TOOL ---

SEARCH_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="search_memory",
            description="Search past conversations in memory.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "query": types.Schema(
                        type="STRING",
                        description="Search keyword"
                    )
                },
                required=["query"]
            )
        )
    ]
)


# --- SYSTEM PROMPT ---

SYSTEM_PROMPT = """
Sen Nova AI'sın, yardımcı bir yapay zeka asistanısın.

- Kullanıcının istediği uzunlukta cevap ver.
- Kullanıcı uzun bir yazı isterse eksiksiz yaz.
- Kullanıcı kısa cevap isterse kısa cevap ver.
- Kod yazarken eksik bırakma.
- Gereksiz emoji kullanma.
- Geçmiş konuşmalar sorulursa search_memory toolunu kullan.
"""


# --- MODEL NAME ---

def get_model():
    return MODEL

# --- CORE AI LOOP (FIXED TOOL HANDLING) ---

def create_answer(user_message: str):
    recent = get_recent_messages(20)

    history = "\n".join(
        f"{m['role']}: {m['content']}" for m in recent
    )

    user_content = f"[History]\n{history}\n\n[User]\n{user_message}"

    messages = [
        {"role": "user", "parts": [{"text": user_content}]}
    ]

    while True:
        response = gemini_client.models.generate_content(
            model=get_model(),
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[SEARCH_TOOL],
                max_output_tokens=8192,
            )
        )

        part = response.candidates[0].content.parts[0]

        # --- TOOL CALL ---
        if getattr(part, "function_call", None):
            fn = part.function_call
            query = fn.args.get("query", "")

            print(f"\n[Memory search: {query}]")

            results = search_messages(query)

            if results:
                result_text = "\n".join(
                    f"{r['role']}: {r['content']}"
                    for r in results
                )
            else:
                result_text = "No results."

            messages.append(response.candidates[0].content)

            messages.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_function_response(
                            name=fn.name,
                            response={"result": result_text}
                        )
                    ]
                )
            )

            continue

        response = gemini_client.models.generate_content(
            model=get_model(),
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[SEARCH_TOOL],
            )
        )

        return response.text

# --- MAIN ---

if __name__ == "__main__":
    init_db()
    print("Nova AI Başlatıldı 🚀")