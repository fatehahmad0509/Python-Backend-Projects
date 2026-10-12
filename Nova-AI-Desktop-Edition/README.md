# Nova AI (Desktop Edition)

Nova AI is a desktop AI assistant powered by Google Gemini with persistent memory (it remembers past conversations). It runs through a modern chat interface built with PySide6; conversations are stored in a local SQLite database, and the model can search past messages when needed.

> The application is meant to be run only through the desktop interface (`ui.py`). `main.py` is a backend module that holds the DB and Gemini functions used by the UI; it is not designed to be run directly.

## Features

- **Desktop interface:** A PySide6 GUI with dark/light themes, streaming responses, user/assistant chat bubbles, and a welcome screen.
- **Conversation memory:** All messages are stored in a local SQLite database called `nova_memory.db`, and history is automatically loaded every time the app starts.
- **History search (tool calling):** When the user asks about a past topic, the model can call the `search_memory` tool to search the database.
- **Settings window:** The API key, model, and theme can be changed from within the app and are saved to `settings.json`.
- **Error handling:** User-friendly error messages for cases like an invalid API key, quota exhaustion, or connection errors.
- **Logo support:** If a logo is found in the project folder, it is used as both the assistant avatar and the window icon.

## Requirements

- Python 3.10 or higher
- A valid Google Gemini API key
- An operating system that supports PySide6 (Windows / macOS / Linux)

## Installation

1. Clone the repository or download the files into a folder.
2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```
5. Set up your API key. You can do this in two ways:

   - **From within the app:** Run the application and open the Settings window (top right) to enter and save your API key, model, and theme.
   - **Manually:** Edit the `settings.json` file directly:

     ```json
     {
         "api_key": "ENTER_YOUR_OWN_API_KEY_HERE",
         "model": "gemini-2.0-flash-lite",
         "theme": "dark"
     }
     ```

   > ⚠️ **Security warning:** `settings.json` stores your API key in plain text. Never push this file to a public repository — add it to `.gitignore`. If a key has already been exposed in the repo, revoke it immediately and generate a new one.

## Usage

To start the application:

```bash
python ui.py
```

When the window opens, any previously saved conversation history is loaded automatically; otherwise the welcome screen is shown. Type your message into the input box at the bottom and send it; the response will be streamed to the screen.

## Project Structure

```
.
├── ui.py                # The application's single entry point — PySide6 desktop interface
├── main.py              # Backend module: DB operations, Gemini integration, and the search_memory tool (used by ui.py, not run directly)
├── settings.py           # Settings manager class that reads/writes settings.json
├── settings.json          # Configuration values such as model, theme, and API key
├── requirements.txt        # Python dependencies
├── logo.jpeg               # (optional) Application logo / avatar image
└── nova_memory.db           # (created automatically) SQLite database where conversation history is stored
```

## How It Works

1. When `ui.py` starts, the SQLite database is created (if it doesn't already exist) via `init_db()` in `main.py`.
2. The user's message is saved to the database and sent to the model along with the last 20 messages.
3. If the model wants to look something up in the history, it calls the `search_memory` function; `search_messages()` then searches the database and the result is sent back to the model.
4. The response is streamed in via `generate_content_stream` and written to the interface chunk by chunk.
5. The final response is saved to the database and displayed in the chat window.

## Notes

- The line `self.settings = self.data` in `settings.py` is kept for backward compatibility.
- The `.env` file is loaded via `python-dotenv`; you can add additional environment variables there if needed.
- The PySide6 interface runs on Windows, macOS, and Linux; on some Linux distributions, additional system libraries (e.g. `libxcb`) may be required.
