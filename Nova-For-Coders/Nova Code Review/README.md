# Nova Code Review

Nova Code Review is an automated utility designed to scan local project directories, generate a structured map of the codebase, and leverage Google's Gemini AI to provide intelligent code reviews and insights.

## ✨ Features
*   **Intelligent Project Scanning**: Recursively traverses project directories while automatically ignoring irrelevant folders (e.g., `.git`, `node_modules`, `venv`).
*   **Smart Filtering**: Filters files by readable extensions to ensure only relevant source code is processed.
*   **AI-Powered Analysis**: Integrates with the Google Gemini API to analyze project structure and code contents.
*   **Safety Limits**: Built-in constraints for file size, total file counts, and character limits to manage API usage effectively.

## 🛠 Tech Stack
*   **Language**: Python 3
*   **AI/LLM**: Google Generative AI (Gemini SDK)
*   **Environment Management**: `python-dotenv`

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/nova-code-review.git
   cd "Nova Code Review"
   ```

2. Install dependencies:
   ```bash
   pip install google-generativeai python-dotenv
   ```

3. Set up your environment variables:
   Create a `.env` file in the root directory and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```

## 💻 Usage

Run the script by pointing it to the directory you wish to analyze:

```bash
python main.py /path/to/your/project
```

The script will scan the target directory, map the file structure, and prepare the content for AI-driven review based on the configuration logic defined in `main.py`.

## 📁 Project Structure

```text
Nova Code Review/
├── main.py        # Core logic for scanning and AI integration
└── .env           # Environment variables (not tracked in git)
```

## ⚙️ Configuration

The `main.py` file contains several constants that define the behavior of the scanner:

*   **`READABLE_EXTENSIONS`**: Defines which file types are processed.
*   **`SKIP_DIRS`**: A blacklist of directories to exclude from scanning (e.g., build artifacts, dependency folders).
*   **`MAX_FILE_SIZE_KB`**: Maximum size of a single file to be included.
*   **`MAX_FILES`**: Cap on the number of files analyzed to prevent context window overflow.

## 📄 License
This project is licensed under the MIT License.