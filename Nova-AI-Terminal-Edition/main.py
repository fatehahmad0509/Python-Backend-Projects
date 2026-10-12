import os
import sqlite3
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

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

def get_recent_messages(limit: int = 20) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT role, content, timestamp FROM messages ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in reversed(rows)]

def search_messages(query: str) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT role, content, timestamp FROM messages WHERE content LIKE ? ORDER BY id DESC LIMIT 15",
        (f"%{query}%",)
    )
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in rows]

def get_all_messages() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role, content, timestamp FROM messages ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in rows]

def export_history_md() -> str:
    all_messages = get_all_messages()
    filename = os.path.join(BASE_DIR, f"nova_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")

    lines = [
        "# Nova AI Chat History",
        f"*Exported: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}*",
        f"*Total messages: {len(all_messages)}*",
        "",
        "---",
        "",
    ]

    for m in all_messages:
        time = datetime.fromisoformat(m["timestamp"]).strftime("%d.%m.%Y %H:%M")
        if m["role"] == "User":
            lines.append(f"### 🧑 User — *{time}*")
        else:
            lines.append(f"### 🤖 Nova AI — *{time}*")
        lines.append(m["content"])
        lines.append("")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filename

# --- Tool Definition ---

SEARCH_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="search_memory",
            description=(
                "Searches the database for the user's past conversations. "
                "Use this tool when the user refers to something they previously mentioned, "
                "said, asked, or discussed."
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "query": types.Schema(
                        type="STRING",
                        description="The word or phrase to search for"
                    )
                },
                required=["query"]
            )
        )
    ]
)

# --- AI ---

SYSTEM_PROMPT = """You are Nova AI, an AI assistant living in the user's terminal.
Give short and clear responses, no emojis, don't be overly brief but don't ramble either — 1-2 sentences is enough.

Commands:
/exit           - quit
/history        - export history to .md file
/search <word>  - search history manually
/commands       - show command list
/clearterminal  - clear terminal

If the user is asking about something discussed previously, or uses phrases like
'earlier', 'before', 'do you remember', 'I told you', use the search_memory tool."""


def stream_print(stream) -> str:
    print("Nova AI: ", end="", flush=True)
    full_text = ""
    for chunk in stream:
        if chunk.text:
            print(chunk.text, end="", flush=True)
            full_text += chunk.text
    print()
    return full_text.strip()


def create_answer(user_message: str) -> str | None:
    recent = get_recent_messages(20)
    history_lines = [f"{m['role']}: {m['content']}" for m in recent]
    history_text = "\n".join(history_lines)

    user_content = f"[Last 20 messages]\n{history_text}\n\n[New message]\n{user_message}"

    messages = [{"role": "user", "parts": [{"text": user_content}]}]

    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[SEARCH_TOOL],
            )
        )

        part = response.candidates[0].content.parts[0]

        if part.function_call:
            fn = part.function_call
            query = fn.args.get("query", "")

            print(f"[Nova AI is searching memory: '{query}']")
            results = search_messages(query)

            if results:
                result_lines = [
                    f"[{r['timestamp'][:16]}] {r['role']}: {r['content']}"
                    for r in results
                ]
                result_text = "\n".join(result_lines)
            else:
                result_text = "No results found."

            messages.append(response.candidates[0].content)
            messages.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_function_response(
                        name=fn.name,
                        response={"result": result_text}
                    )]
                )
            )

            stream = gemini_client.models.generate_content_stream(
                model="gemini-3.1-flash-lite",
                contents=messages,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                )
            )
            return stream_print(stream)

        stream = gemini_client.models.generate_content_stream(
            model="gemini-3.1-flash-lite",
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[SEARCH_TOOL],
            )
        )
        return stream_print(stream)

    except Exception as e:
        print(f"Error: {e}")
        return None


# --- Main ---

init_db()
print("--Nova AI Started--")

while True:
    user_message = input("User: ").strip()

    if not user_message:
        continue

    if user_message == "/exit":
        quit()

    elif user_message == "/clearterminal":
        os.system("cls" if os.name == "nt" else "clear")
        print("--Nova AI Terminal Cleared!--")
        continue

    elif user_message == "/history":
        file = export_history_md()
        print(f"History exported: {file}")
        continue

    elif user_message.startswith("/search "):
        query = user_message[8:].strip()
        if not query:
            print("Usage: /search <word>")
            continue
        results = search_messages(query)
        print(f"--{len(results)} result(s) for '{query}'--")
        if not results:
            print("(no results found)")
        for m in results:
            print(f"[{m['timestamp'][:16]}] {m['role']}: {m['content']}")
        print()
        continue

    elif user_message == "/commands":
        print("""--Nova AI Command List--

/exit             - Close the application
/history          - Export history to .md file
/search <word>    - Search history manually
/commands         - Show this menu
/clearterminal    - Clear the terminal
""")
        continue

    save_message("User", user_message)
    answer = create_answer(user_message)

    if answer:
        save_message("Nova AI", answer)
