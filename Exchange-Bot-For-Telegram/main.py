import os
import logging
import threading
import asyncio
import psycopg2
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- KEEP-ALIVE SERVER ---
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot is alive!", 200

# --- DATABASE ENGINE ---
def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")

def init_db():
    conn = get_conn(); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tracking (user_id BIGINT, asset TEXT, UNIQUE(user_id, asset))''')
    c.execute('''CREATE TABLE IF NOT EXISTS portfolio (user_id BIGINT, asset TEXT, amount NUMERIC, UNIQUE(user_id, asset))''')
    c.execute('''CREATE TABLE IF NOT EXISTS whitelist (user_id BIGINT PRIMARY KEY)''')
    conn.commit(); conn.close()

def is_allowed(user_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT 1 FROM whitelist WHERE user_id = %s", (user_id,))
    res = c.fetchone(); conn.close(); return res is not None

def whitelist_add(user_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO whitelist (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))
    conn.commit(); conn.close()

def whitelist_remove(user_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("DELETE FROM whitelist WHERE user_id = %s", (user_id,))
    conn.commit(); conn.close()

def whitelist_load():
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT user_id FROM whitelist")
    rows = c.fetchall(); conn.close(); return [row[0] for row in rows]

def portfolio_set(user_id, asset, amount):
    conn = get_conn(); c = conn.cursor()
    c.execute("""INSERT INTO portfolio (user_id, asset, amount) VALUES (%s, %s, %s)
                 ON CONFLICT (user_id, asset) DO UPDATE SET amount = EXCLUDED.amount""", (user_id, asset, amount))
    conn.commit(); conn.close()

def portfolio_remove(user_id, asset):
    conn = get_conn(); c = conn.cursor()
    c.execute("DELETE FROM portfolio WHERE user_id = %s AND asset = %s", (user_id, asset))
    conn.commit(); conn.close()

def portfolio_load(user_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT asset, amount FROM portfolio WHERE user_id = %s", (user_id,))
    rows = c.fetchall(); conn.close(); return {row[0]: float(row[1]) for row in rows}

def save_to_db(user_id, asset):
    conn = get_conn(); c = conn.cursor()
    c.execute("INSERT INTO tracking (user_id, asset) VALUES (%s, %s) ON CONFLICT DO NOTHING", (user_id, asset))
    conn.commit(); conn.close()

def remove_from_db(user_id, asset):
    conn = get_conn(); c = conn.cursor()
    c.execute("DELETE FROM tracking WHERE user_id = %s AND asset = %s", (user_id, asset))
    conn.commit(); conn.close()

def load_all_from_db():
    temp_db = {}
    try:
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT user_id, asset FROM tracking")
        for uid, ast in c.fetchall():
            temp_db.setdefault(uid, []).append(ast)
        conn.close()
    except Exception as e: logger.warning(f"load_all error: {e}")
    return temp_db

init_db()
tracking_db = load_all_from_db()
last_prices = {}
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

async def check_access(update: Update) -> bool:
    uid = update.effective_user.id
    if uid == ADMIN_ID or is_allowed(uid): return True
    await update.message.reply_text("🚫YOU HAVE NO AUTHORITY TO USE THIS COMMAND")
    return False

exchanges = {
    "dollar": ["USDTRY=X", "TL"],
    "euro": ["EURTRY=X", "TL"],
    "sterling": ["GBPTRY=X", "TL"],
    "swiss_franc": ["CHFTRY=X", "TL"],
    "canadian_dollar": ["CADTRY=X", "TL"],
    "australian_dollar": ["AUDTRY=X", "TL"],
    "japanese_yen": ["JPYTRY=X", "TL"],
    "kuwaiti_dinar": ["KWDTRY=X", "TL"],
    "saudi_riyal": ["SARTRY=X", "TL"],
    "dxy": ["DX-Y.NYB", "USD"], 

    "bitcoin": ["BTC-USD", "USD"],
    "ethereum": ["ETH-USD", "USD"],
    "solana": ["SOL-USD", "USD"],
    "binance_coin": ["BNB-USD", "USD"],
    "ripple": ["XRP-USD", "USD"],
    "dogecoin": ["DOGE-USD", "USD"],
    "cardano": ["ADA-USD", "USD"],
    "avalanche": ["AVAX-USD", "USD"],
    "polkadot": ["DOT-USD", "USD"],
    "chainlink": ["LINK-USD", "USD"],
    "shiba": ["SHIB-USD", "USD"],
    "pepe": ["PEPE-USD", "USD"],
    "near": ["NEAR-USD", "USD"],
    "toncoin": ["TON-USD", "USD"],
    "aptos": ["APT-USD", "USD"],

    "thy": ["THYAO.IS", "TL"],
    "aselsan": ["ASELS.IS", "TL"],
    "eregli": ["EREGL.IS", "TL"],
    "tupras": ["TUPRS.IS", "TL"],
    "sise_cam": ["SISE.IS", "TL"],
    "apple": ["AAPL", "USD"],
    "tesla": ["TSLA", "USD"],
    "nvidia": ["NVDA", "USD"],
    "amazon": ["AMZN", "USD"],
    "google": ["GOOGL", "USD"],
    "microsoft": ["MSFT", "USD"],
    "meta": ["META", "USD"],
    "netflix": ["NFLX", "USD"],
    "alibaba": ["BABA", "USD"],
    "microstrategy": ["MSTR", "USD"],

    "gold_ounce": ["GC=F", "USD"],
    "silver": ["SI=F", "USD"],
    "brent_oil": ["BZ=F", "USD"],
    "natural_gas": ["NG=F", "USD"],
    "copper": ["HG=F", "USD"]
}

def fetch_yahoo_price(symbol):
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            d = r.json()['chart']['result'][0]['meta']
            return float(d['regularMarketPrice']), d.get('currency', 'USD').replace("TRL", "TL")
    except: pass
    return None, None

async def get_live_price(asset):
    asset = asset.upper().strip() 
    query = asset.lower()
    
    if any(x in query for x in ["gold gram", "gold quarter", "altın"]):
        ons, _ = fetch_yahoo_price("GC=F")
        usd, _ = fetch_yahoo_price("USDTRY=X")
        if ons and usd:
            gram = (ons / 31.1035) * usd
            return (gram * 1.63 if "quarter" in query else gram), "TL"
            
    sym = next((v[0] for k, v in exchanges.items() if k == query), asset)
    return fetch_yahoo_price(sym)

# --- BOT COMMANDS ---
async def list_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update): return
    text = (
        "🤖 *Market Bot v2.0 - Command List*\n\n"
        "• `/exchanges` - List all available assets\n"
        "• `/track [asset]` - Add asset to your alert list\n"
        "• `/untrack [asset]` - Remove asset from alert list\n"
        "• `/list` - View your alert list\n"
        "• `/guess [asset]` - Get 20-day trend prediction\n\n"
        "💼 *Portfolio*\n"
        "• `/padd [asset] [amount]` - Add amount to portfolio (stacks)\n"
        "• `/pset [asset] [amount]` - Set exact amount in portfolio\n"
        "• `/pdel [asset]` - Remove asset from portfolio\n"
        "• `/portfolio` - Show portfolio with live values\n\n"
        "• `/commands` - Show this help menu"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def wladd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args: return await update.message.reply_text("Usage: `/wladd ID`", parse_mode="Markdown")
    whitelist_add(int(context.args[0]))
    await update.message.reply_text(f"✅ `{context.args[0]}` Added.")

async def wlremove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args: return
    whitelist_remove(int(context.args[0]))
    await update.message.reply_text(f"🗑 `{context.args[0]}` Removed.")

async def wllist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    ids = whitelist_load()
    await update.message.reply_text("👥 *Whitelist:*\n" + "\n".join(f"`{i}`" for i in ids) if ids else "Boş.")

async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update): return
    if not context.args: return
    user_input = " ".join(context.args).lower().strip()
    asset = "gold quarter" if "quarter" in user_input else "gold gram" if any(x in user_input for x in ["gold", "altın", "gram"]) else user_input if user_input in exchanges else None
    
    if asset:
        uid = update.effective_user.id
        tracking_db.setdefault(uid, [])
        if asset not in tracking_db[uid]:
            tracking_db[uid].append(asset)
            save_to_db(uid, asset)
            await update.message.reply_text(f"✅ {asset.upper()} added.")
        else: await update.message.reply_text("Already in your list.")
    else: await update.message.reply_text("Asset not found.")

async def untrack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update): return
    if not context.args: return
    user_input = " ".join(context.args).lower().strip()
    asset = "gold quarter" if "quarter" in user_input else "gold gram" if any(x in user_input for x in ["gold", "altın", "gram"]) else user_input
    
    uid = update.effective_user.id
    if uid in tracking_db and asset in tracking_db[uid]:
        tracking_db[uid].remove(asset)
        remove_from_db(uid, asset)
        await update.message.reply_text(f"❌ {asset.upper()} removed.")

async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update): return
    ulist = tracking_db.get(update.effective_user.id, [])
    await update.message.reply_text(f"📋 *Your List:* {', '.join(ulist).upper()}" if ulist else "Empty.")

async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update) or not context.args: return
    user_input = " ".join(context.args).lower()
    sym = "GC=F" if any(x in user_input for x in ["gold", "altın", "gram"]) else (exchanges[user_input][0] if user_input in exchanges else None)
    
    if sym:
        await update.message.reply_text("Analyzing market trends...")
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=20d"
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).json()
            closes = r['chart']['result'][0]['indicators']['quote'][0]['close']
            closes = [c for c in closes if c is not None]
            trend = "🚀 UPWARD" if sum(closes[-5:])/5 > sum(closes)/len(closes) else "🔻 DOWNWARD"
            await update.message.reply_text(f"Prediction for *{user_input.upper()}*: {trend}", parse_mode="Markdown")
        except: await update.message.reply_text("Trend analizi yapılamadı.")

def parse_asset(user_input):
    if user_input in exchanges or user_input in ["gold gram", "gold quarter"]: return user_input
    if any(x in user_input for x in ["gold", "altın", "gram", "quarter"]):
        return "gold quarter" if "quarter" in user_input else "gold gram"
    return None

async def portfolio_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update) or len(context.args) < 2: return
    try: amt = float(context.args[-1])
    except: return
    ast = parse_asset(" ".join(context.args[:-1]).lower().strip())
    if not ast: return
    uid = update.effective_user.id
    new_amt = portfolio_load(uid).get(ast, 0.0) + amt
    portfolio_set(uid, ast, new_amt)
    await update.message.reply_text(f"✅ *{ast.upper()}*: {amt} added → Total: *{new_amt:.4g}*", parse_mode="Markdown")

async def portfolio_set_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update) or len(context.args) < 2: return
    try: amt = float(context.args[-1])
    except: return
    ast = parse_asset(" ".join(context.args[:-1]).lower().strip())
    if not ast: return
    portfolio_set(update.effective_user.id, ast, amt)
    await update.message.reply_text(f"✅ *{ast.upper()}* set to *{amt:.4g}*.", parse_mode="Markdown")

async def portfolio_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update) or not context.args: return
    ui = " ".join(context.args).lower().strip()
    ast = parse_asset(ui) or ui
    portfolio_remove(update.effective_user.id, ast)
    await update.message.reply_text(f"🗑 *{ast.upper()}* removed.")

async def portfolio_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update): return
    holdings = portfolio_load(update.effective_user.id)
    if not holdings: return await update.message.reply_text("📭 Portfolio empty.")
    
    await update.message.reply_text("⏳ Fetching live prices...")
    lines = []; total_usd = 0.0; total_tl = 0.0
    usd_to_tl, _ = fetch_yahoo_price("USDTRY=X")

    for ast, amt in holdings.items():
        pr, un = await get_live_price(ast)
        if not pr:
            lines.append(f"• *{ast.upper()}*: {amt} × _(unavailable)_")
            continue
        val = pr * amt
        if un == "USD":
            total_usd += val
            if usd_to_tl: total_tl += val * usd_to_tl
            lines.append(f"• *{ast.upper()}*: {amt:.4g} × {pr:,.2f} USD = *{val:,.2f} USD*")
        else:
            total_tl += val
            if usd_to_tl: total_usd += val / usd_to_tl
            lines.append(f"• *{ast.upper()}*: {amt:.4g} × {pr:,.2f} TL = *{val:,.2f} TL*")

    msg = "📊 *Your Portfolio*\n\n" + "\n".join(lines) + f"\n\n💼 *Total:*\n  • {total_usd:,.2f} USD" + (f"\n  ({total_tl:,.2f} TL)" if usd_to_tl else "")
    await update.message.reply_text(msg, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update): return
    text = update.message.text.lower().strip()
    pr, un = await get_live_price(text)
    if pr: await update.message.reply_text(f"💰 {text.capitalize()}: {pr:,.2f} {un}")

async def price_checker(context: ContextTypes.DEFAULT_TYPE):
    for asset in list(exchanges.keys()) + ["gold gram"]:
        current, unit = await get_live_price(asset)
        if current and asset in last_prices:
            old = last_prices[asset]
            if abs((current - old) / old) >= 0.001:
                for uid, uassets in tracking_db.items():
                    if asset in uassets:
                        direction = "🚀" if current > old else "🔻"
                        try: await context.bot.send_message(chat_id=uid, text=f"🔔 *ALERT:* {asset.upper()} is {current:,.2f} {unit} ({direction}), Change: 0.05%", parse_mode="Markdown")
                        except: pass
        if current: last_prices[asset] = current

async def start_bot():
    app = Application.builder().token(os.environ["BOT_TOKEN"]).build()
    
    app.add_handler(CommandHandler("start", list_commands))
    app.add_handler(CommandHandler("commands", list_commands))
    app.add_handler(CommandHandler("exchanges", lambda u, c: u.message.reply_text("📋 Assets:\n• " + "\n• ".join(list(exchanges.keys()) + ["gold gram", "gold quarter"]))))
    app.add_handler(CommandHandler("track", track))
    app.add_handler(CommandHandler("untrack", untrack))
    app.add_handler(CommandHandler("list", show_list))
    app.add_handler(CommandHandler("guess", guess))
    app.add_handler(CommandHandler("padd", portfolio_add))
    app.add_handler(CommandHandler("pset", portfolio_set_cmd))
    app.add_handler(CommandHandler("pdel", portfolio_del))
    app.add_handler(CommandHandler("portfolio", portfolio_show))
    app.add_handler(CommandHandler("wladd", wladd))
    app.add_handler(CommandHandler("wlremove", wlremove))
    app.add_handler(CommandHandler("wllist", wllist))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    if app.job_queue:
        app.job_queue.run_repeating(price_checker, interval=300, first=10)

    logger.info("--- GLOBAL BOT v2.1 IS LIVE ---")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

if __name__ == '__main__':
    threading.Thread(target=lambda: asyncio.run(start_bot()), daemon=True).start()
    flask_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
