import json
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)

# 🔴 اینجا فقط خودت مقدار بده
TOKEN = "8619139040:AAEdkFLQiA3Qwzf2bVSiLNWu_qZSWngttzA"
ADMIN_ID = 8732340675  # آیدی عددی خودت

SUPPORT_ID = '@your_support_id'
CARD_NUMBER = '6221061258771031'
CARD_OWNER = 'ایروانی'

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

plans = {
    '1 گیگ - یک ماهه': 400,
    '2 گیگ - یک ماهه': 800,
    '3 گیگ - یک ماهه': 1200,
    '4 گیگ - یک ماهه': 1600,
    '5 گیگ - یک ماهه': 2000,
}
plan_list = list(plans.keys())

# ---------- ذخیره فایل ----------

def load_data():
    try:
        with open('data.json', 'r') as f:
            return json.load(f)
    except:
        return {
            "configs": {p: [] for p in plans},
            "sales": []
        }

def save_data():
    with open('data.json', 'w') as f:
        json.dump(data, f)

data = load_data()
configs = data["configs"]
sales = data["sales"]

cart = {}
pending_orders = {}
shop_open = True

# ---------- کیبورد ----------

def main_keyboard(uid):
    kb = [
        ['🛒 خرید VPN'],
        ['📦 پلن‌ها'],
        ['🗑 سبد خرید'],
        ['📞 پشتیبانی'],
    ]
    if uid == ADMIN_ID:
        kb.append(['🛠 پنل ادمین'])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('📦 استاک', callback_data='stock')],
        [InlineKeyboardButton('📊 آمار', callback_data='stats')],
        [InlineKeyboardButton('💾 بکاپ', callback_data='backup')],
    ])

# ---------- start ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋 به ربات خوش اومدی",
        reply_markup=main_keyboard(update.effective_user.id)
    )

# ---------- add سریع ----------

async def add_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        cmd = update.message.text.split()[0]
        config = update.message.text.replace(cmd, "").strip()

        mapping = {
            '/add1': plan_list[0],
            '/add2': plan_list[1],
            '/add3': plan_list[2],
            '/add4': plan_list[3],
            '/add5': plan_list[4],
        }

        plan = mapping.get(cmd)

        if not plan or not config:
            await update.message.reply_text("❌ فرمت اشتباه")
            return

        configs[plan].append(config)
        save_data()

        await update.message.reply_text(f"✅ اضافه شد\n📦 {len(configs[plan])}")

    except:
        await update.message.reply_text("❌ خطا")

# ---------- متن ----------

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global shop_open

    text = update.message.text
    uid = update.effective_user.id

    if text == '📞 پشتیبانی':
        await update.message.reply_text(SUPPORT_ID)
        return

    if text == '📦 پلن‌ها':
        msg = "📦 پلن‌ها:\n\n"
        for p, price in plans.items():
            msg += f"{p}: {price} تومان\n"
        await update.message.reply_text(msg)
        return

    if text == '🛒 خرید VPN':
        if not shop_open:
            await update.message.reply_text("🔴 فروش بسته است")
            return

        kb = [[p] for p in plans]
        await update.message.reply_text(
            "پلن انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return

    if text in plans:
        if len(configs[text]) == 0:
            await update.message.reply_text("❌ موجود نیست")
            return

        cart.setdefault(uid, {})
        cart[uid][text] = cart[uid].get(text, 0) + 1

        await update.message.reply_text(
            f"{text} اضافه شد\n\n💳 `{CARD_NUMBER}`",
            parse_mode="Markdown"
        )
        return

    if text == '🗑 سبد خرید':
        if uid not in cart:
            await update.message.reply_text("خالیه")
            return

        msg = ""
        total = 0

        for p, c in cart[uid].items():
            msg += f"{p} x{c}\n"
            total += plans[p] * c

        msg += f"\n💰 {total}"

        await update.message.reply_text(msg)
        return

    if text == '🛠 پنل ادمین' and uid == ADMIN_ID:
        await update.message.reply_text("پنل:", reply_markup=admin_keyboard())

# ---------- عکس ----------

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in cart:
        return

    pending_orders[uid] = cart[uid]

    await context.bot.send_message(
        ADMIN_ID,
        f"رسید از {uid}"
    )

    await update.message.reply_text("منتظر تایید")

# ---------- اجرا ----------

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CommandHandler("add1", add_config))
    app.add_handler(CommandHandler("add2", add_config))
    app.add_handler(CommandHandler("add3", add_config))
    app.add_handler(CommandHandler("add4", add_config))
    app.add_handler(CommandHandler("add5", add_config))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
