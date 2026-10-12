# Nova AI — Terminal Edition

A memory-enabled AI assistant that runs in your terminal. Powered by Google Gemini, stores conversation history with SQLite.

---

## Setup

### 1. Requirements

- Python 3.10+
- Pip packages:

```bash
pip install google-genai python-dotenv
```

### 2. API Key

Create a `.env` file in the project folder:

```
GEMINI_API_KEY=your_api_key_here
```

Get one for free at: https://aistudio.google.com/app/apikey

### 3. Edit `nova.bat`

Update the path inside `nova.bat` to point to your `main.py`:

```bat
@echo off
py "C:\Path\To\Your\main.py"
```

### 4. Add to Environment Variables

Place `nova.bat` in `C:\scripts` (create the folder if it doesn't exist), then add it to PATH:

1. `Win + S` → search "Environment Variables" → open
2. Under **User variables**, select `Path` → **Edit**
3. **New** → type `C:\scripts` → OK

Restart your terminal. Now you can launch Nova from anywhere:

```
nova
```

---

## Usage

```
nova
```

### Commands

| Command | Description |
|---|---|
| `/exit` | Closes the application |
| `/history` | Exports chat history to a `.md` file |
| `/search <word>` | Searches through past conversations |
| `/commands` | Shows the command list |
| `/clearterminal` | Clears the terminal |

---

## Features

- **Memory** — All conversations are stored in a SQLite database (`nova_memory.db`)
- **Smart search** — Phrases like "I mentioned earlier..." trigger automatic memory search
- **Streaming** — Responses stream character by character
- **History export** — `/history` generates a Markdown file

---

## File Structure

```
Nova AI (Terminal Edition)/
├── main.py           # Main application
├── nova.bat          # Launcher (added to PATH)
├── .env              # API key (don't commit this!)
└── nova_memory.db    # Created automatically
```

---

## Notes

- Never share or commit your `.env` file to Git
- Deleting `nova_memory.db` resets all conversation history
