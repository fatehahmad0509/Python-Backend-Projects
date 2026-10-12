🌍 Exchange.Com – Currency Exchange Tracker

A simple Python desktop application + CLI script that fetches real-time currency exchange rates and displays them in a clean GUI built with CustomTkinter.

It supports multiple currencies and converts them into TRY (Turkish Lira) using live data from an external API.

🚀 Features
🌐 Real-time exchange rates via API
🖥️ Modern GUI using customtkinter
🏳️ Country flags for currencies
📊 Currency values converted to TRY
🔄 Manual refresh button
⚡ Threaded API requests (no UI freezing)
🧾 Bonus CLI version for terminal output
📦 Supported Currencies
USD 🇺🇸
EUR 🇪🇺
GBP 🇬🇧
AZN 🇦🇿
JPY 🇯🇵
CHF 🇨🇭
AUD 🇦🇺
CAD 🇨🇦
CNY 🇨🇳
NZD 🇳🇿

All values are converted to TRY (₺).

🧠 How It Works

The app uses the ExchangeRate API:

https://v6.exchangerate-api.com
Base currency: USD
All other currencies are calculated using USD → TRY ratio

Example formula:

EUR → TRY = (USD → TRY) / (USD → EUR)
🖥️ GUI Preview

Built with:

CustomTkinter
PIL (Pillow)
Requests
Threading

Features:

Sidebar navigation
Currency cards grid
Flag icons (API or local images)
Live update button
🧰 Installation
1. Clone repo
git clone https://github.com/yourusername/exchange-com.git
cd exchange-com
2. Install dependencies
pip install customtkinter requests pillow
3. Run GUI app
python main.py
4. Run CLI version
python cli.py
📁 Project Structure
exchange-com/
│
├── main.py        # GUI application
├── cli.py         # Terminal version
├── assets/        # Flag images (optional)
└── README.md
⚠️ Notes
Requires internet connection
API key is currently hardcoded (recommended to move to .env)
Free API limits may apply
🔮 Future Improvements
🔐 Move API key to environment variables
📉 Add historical charts
💱 Add currency converter input (amount-based conversion)
🌙 Dark/light mode switch
📱 Convert into mobile app (Kivy / Flutter bridge)
👨‍💻 Author

Made with 💻 + ☕ by a developer who clearly enjoys watching currencies fluctuate like a stock market rollercoaster 🎢
