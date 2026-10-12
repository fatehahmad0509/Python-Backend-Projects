# 🤖 Nova Readme Gen

> AI-Powered README Generator — scans your project and generates a professional `README.md` using Google Gemini AI.

---

## ✨ Features

- 📂 Recursively scans your project directory
- 🧠 Sends file structure and partial file contents to Gemini AI for analysis
- 📝 Generates a complete, well-structured `README.md` in Markdown format
- ⚡ Prioritizes important config files (`package.json`, `requirements.txt`, `Dockerfile`, etc.)
- 🚫 Automatically skips irrelevant directories (`node_modules`, `.git`, `__pycache__`, etc.)
- ⚠️ Warns before overwriting an existing `README.md`

---

## 🛠️ Tech Stack

- **Python 3**
- **Google Gemini AI** (`google-genai`)
- **python-dotenv**

---

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/nova-readme-gen.git
   cd nova-readme-gen
   ```

2. Install dependencies:
   ```bash
   pip install google-genai python-dotenv
   ```

3. Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

---

## 🚀 Usage

**Run with a path argument:**
```bash
python main.py /path/to/your/project
```

**Run interactively:**
```bash
python main.py
# Then enter the project folder path when prompted
# Press Enter to use the current directory
```

The generated `README.md` will be saved directly into the target project folder.

---

## ⚙️ Configuration

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key (required) |

You can get a Gemini API key from [Google AI Studio](https://aistudio.google.com/).

---

## 📁 Project Structure

```
nova-readme-gen/
├── main.py        # Main script
├── .env           # Environment variables (not committed)
└── README.md      # This file
```

---

## 🔧 Limits & Defaults

| Setting | Value |
|---|---|
| Max file size | 30 KB per file |
| Max files scanned | 40 |
| Max content sent to AI | 12,000 characters |
| Max snippet per file | 1,500 characters |

---

## 📄 License

MIT License — feel free to use and modify.