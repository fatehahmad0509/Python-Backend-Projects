# 🤖 Nova for Coders

> A collection of AI-powered CLI tools for developers — built with Python and Google Gemini AI.

---

## 🧰 Tools

### 📝 [Nova Readme Gen](./nova-readme-gen)
Scans your project directory and automatically generates a professional `README.md` using Gemini AI.

- Recursively maps your project structure
- Prioritizes key config files (`package.json`, `requirements.txt`, `Dockerfile`, etc.)
- Produces clean, well-structured Markdown output

```bash
python main.py /path/to/your/project
```

---

### 🔍 [Nova Code Review](./nova-code-review)
Analyzes your codebase and generates a detailed `CODE_REVIEW.md` report with scores, issues, and recommendations.

- Scans source files across all major languages
- Categorizes issues by severity (Critical / Medium / Minor)
- Scores the project across 6 categories out of 100

```bash
python main.py /path/to/your/project
```

---

### 🛡️ [Nova Web Secure](./nova-web-secure)
Checks a website's security headers and SSL certificate, then returns an AI-generated security score.

- Validates SSL certificate and cookie flags
- Checks HSTS, CSP, X-Frame-Options, and more
- Returns a score out of 100 with a risk level and actionable recommendations

```bash
python main.py
# Enter site address when prompted
```

---

## ⚙️ Setup

All tools share the same setup steps:

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Set your Gemini API key**
```bash
cp .env.example .env
```
Then open `.env` and fill in:
```env
GEMINI_API_KEY=your_api_key_here
```

> Get your free API key at [Google AI Studio](https://aistudio.google.com/)

---

## 🛠️ Tech Stack

- **Python 3.8+**
- **Google Gemini AI** (`google-genai`)
- **python-dotenv**
- **requests** *(Nova Web Secure only)*

---

## 📄 License

MIT License — free to use and modify.