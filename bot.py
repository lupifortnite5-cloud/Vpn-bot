import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

CARD = "6221061258771031"

# وضعیت فروش
shop_open = True

# قیمت‌ها
prices = {
    "1 گیگ": 450,
    "2 گیگ": 820,
    "3 گیگ": 1150,
    "4 گیگ": 1450,
    "5 گیگ": 1750
}

plans = list(prices.keys())

# استاک
configs = {p: [] for p in plans}

# سفارش در انتظار
pending = {}

# ---------------- KEYBOARD ----------------
def main_kb():
    return ReplyKeyboardMarkup(
        [["🛒 خرید", "📦 موجودی"], ["📞 پشتیبانی"]],
        resize_keyboard=True
    )

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋", reply_markup=main_kb())

# ---------------- TEXT ----------------
async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global shop_open
    uid = update.effective_user.id
    t = update.message.text

    if t == "📞 پشتیبانی":
        await update.message.reply_text("@your_support_id")
        return

    if t == "📦 موجودی":
        msg = "📦 موجودی:\n\n"
        for p in plans:
            msg += f"{p}: {len(configs[p])}\n"
        await update.message.reply_text(msg)
        return

    if t == "🛒 خرید":
        if not shop_open:
            await update.message.reply_text("🔴 فروش بسته است")
            return

        kb = [[p] for p in plans]
        await update.message.reply_text(
            "پلن رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return

    # انتخاب پلن
    if t in plans:
        if not shop_open:
            await update.message.reply_text("🔴 فروش بسته است")
            return

        if len(configs[t]) == 0:
            await update.message.reply_text("❌ موجودی این پلن تموم شده")
            return

        pending[uid] = t

        await update.message.reply_text(
            f"📦 {t}\n"
            f"💰 {prices[t]} هزار تومان\n\n"
            f"💳 `{CARD}`\n\n"
            f"📸 رسید رو بفرست",
            parse_mode="Markdown"
        )
        return

# ---------------- PHOTO ----------------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in pending:
        await update.message.reply_text("❌ اول پلن انتخاب کن")
        return

    plan = pending[uid]

    if not shop_open:
        await update.message.reply_text("🔴 فروش بسته است")
        return

    if len(configs[plan]) == 0:
        await update.message.reply_text("❌ موجودی تموم شده")
        return

    config = configs[plan].pop(0)

    await update.message.reply_text(
        f"✅ خرید انجام شد\n\n📦 {plan}\n\n`{config}`",
        parse_mode="Markdown"
    )

    # اطلاع به ادمین
    await context.bot.send_message(
        ADMIN_ID,
        f"📥 فروش جدید\n👤 {uid}\n📦 {plan}"
    )

    del pending[uid]

# ---------------- ADMIN ----------------
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        cmd = update.message.text.split()[0]
        data = update.message.text.split(None, 1)[1]

        index = int(cmd.replace("/add", "")) - 1
        plan = plans[index]

        configs[plan].append(data)

        await update.message.reply_text(f"✅ اضافه شد به {plan}")
    except:
        await update.message.reply_text("❌ فرمت اشتباه")

async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = "📦 استاک:\n\n"
    for p in plans:
        msg += f"{p}: {len(configs[p])}\n"

    await update.message.reply_text(msg)

async def open_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global shop_open
    if update.effective_user.id == ADMIN_ID:
        shop_open = True
        await update.message.reply_text("🟢 فروش باز شد")

async def close_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global shop_open
    if update.effective_user.id == ADMIN_ID:
        shop_open = False
        await update.message.reply_text("🔴 فروش بسته شد")

# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CommandHandler("add1", add))
    app.add_handler(CommandHandler("add2", add))
    app.add_handler(CommandHandler("add3", add))
    app.add_handler(CommandHandler("add4", add))
    app.add_handler(CommandHandler("add5", add))

    app.add_handler(CommandHandler("stock", stock))
    app.add_handler(CommandHandler("open", open_shop))
    app.add_handler(CommandHandler("close", close_shop))

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
