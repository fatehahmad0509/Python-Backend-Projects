# 🤖 Nova Web Secure

**Nova Web Secure** is a terminal-based application that automatically analyzes a website's security headers and provides an AI-powered security score.

---

## 🚀 Features

- 🔒 SSL certificate validity and issuer verification
- 🍪 Cookie security flag analysis (Secure, HttpOnly, SameSite)
- 🛡️ HTTP security header checks (HSTS, CSP, X-Frame-Options, etc.)
- 🤖 Automated security analysis and scoring powered by Gemini AI
- 📊 Security score out of 100 with risk level (Low / Medium / High)
- 💡 Strengths, weaknesses, and actionable recommendations

---

## 📋 Checked Security Headers

| Header | Description |
|---|---|
| `HTTPS` | Encrypted connection check |
| `Strict-Transport-Security` | HSTS enforcement |
| `Content-Security-Policy` | Content security policy |
| `X-Frame-Options` | Clickjacking protection |
| `X-Content-Type-Options` | MIME sniffing protection |
| `Permissions-Policy` | Browser permission policy |
| `Cookie Flags` | Secure, HttpOnly, SameSite |
| `SSL Certificate` | Validity and expiration date |

---

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/nova-web-secure.git
cd nova-web-secure
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create your `.env` file
```bash
cp .env.example .env
```

Open `.env` and add your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```

> Get your Gemini API key at: [Google AI Studio](https://aistudio.google.com/)

---

## ▶️ Usage

```bash
python main.py
```

After the app starts, enter the website address you want to analyze:

```
🤖 Nova Web Secure 🤖 | Enter site address: example.com
```

---

## 📊 Example Output

```
⭐ Security Score: 72/100
🚨 Risk: Low Risk

📝 Summary: The site appears to follow generally good security practices,
            however some headers seem to be missing.

✅ Strengths:
- HTTPS is active
- SSL certificate is valid
- HSTS header is present

❌ Weaknesses:
- Content-Security-Policy header is missing
- X-Frame-Options is not defined

💡 Recommendations:
- Adding a CSP header could help prevent XSS attacks
- Setting X-Frame-Options: DENY would reduce clickjacking risk

📋 Scoring Reasoning:
- HTTPS and SSL presence +20 points
- HSTS header +15 points
- Missing CSP -15 points
- Missing X-Frame-Options -8 points
```

---

## 🔐 Security Note

**Never** push your `.env` file to GitHub. It is already excluded via `.gitignore`.

---

## 📦 Requirements

- Python 3.8+
- Gemini API Key

---

## 📄 License

MIT License — feel free to use it however you like.
