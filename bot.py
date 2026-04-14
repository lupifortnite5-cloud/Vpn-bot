import os
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

CARD_NUMBER = "6221061258771031"
CARD_OWNER = "ایروانی"

shop_open = True

plans = {
    "1 گیگ": 400,
    "2 گیگ": 800,
    "3 گیگ": 1200,
    "4 گیگ": 1600,
    "5 گیگ": 2000,
}

configs = {p: [] for p in plans}
pending_orders = {}

# ----------------- KEYBOARD -----------------
def main_kb():
    return ReplyKeyboardMarkup(
        [["خرید VPN"], ["پلن‌ها"], ["پشتیبانی"]],
        resize_keyboard=True
    )

# ----------------- START -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋", reply_markup=main_kb())

# ----------------- SHOP -----------------
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

# ----------------- STOCK FULL -----------------
async def stock_full(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = "📦 استاک:\n\n"
    for i, (plan, lst) in enumerate(configs.items()):
        msg += f"{i}️⃣ {plan}:\n"
        for idx, cfg in enumerate(lst):
            msg += f"{idx} - {cfg}\n"
        msg += "\n"

    await update.message.reply_text(msg)

# ----------------- ADD CONFIG -----------------
async def add_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        cmd = update.message.text.split()[0]
        cfg = update.message.text.split(" ", 1)[1]

        index = int(cmd.replace("/add", "")) - 1
        plan = list(plans.keys())[index]

        configs[plan].append(cfg)

        await update.message.reply_text(f"✅ اضافه شد به {plan}\n📦 {len(configs[plan])}")

    except:
        await update.message.reply_text("❌ فرمت:\n/add1 config")

# ----------------- REMOVE -----------------
async def remove_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        index = int(context.args[0])
        plan_index = int(context.args[1])

        plan = list(configs.keys())[plan_index]

        removed = configs[plan].pop(index)

        await update.message.reply_text(f"🗑 حذف شد:\n{removed}")

    except:
        await update.message.reply_text("❌ فرمت درست:\n/remove index plan_index")

# ----------------- TEXT -----------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if text == "خرید VPN":
        if not shop_open:
            await update.message.reply_text("🔴 فروش بسته است")
            return

        kb = [[p] for p in plans]
        await update.message.reply_text("پلن انتخاب کن:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    elif text in plans:
        price = plans[text]

        await update.message.reply_text(
            f"📦 {text}\n💰 {price} تومان\n\n"
            f"💳 `{CARD_NUMBER}`\n👤 {CARD_OWNER}\n\n"
            "📸 رسید بفرست",
            parse_mode="Markdown",
            reply_markup=main_kb()
        )

        pending_orders[user.id] = text

    elif text == "پلن‌ها":
        msg = ""
        for p, price in plans.items():
            msg += f"{p} : {price}\n"
        await update.message.reply_text(msg)

    elif text == "پشتیبانی":
        await update.message.reply_text("@TtrustVPN_support")

    else:
        await update.message.reply_text("از منو استفاده کن", reply_markup=main_kb())

# ----------------- RECEIPT -----------------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in pending_orders:
        return

    plan = pending_orders[user.id]

    msg = await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=user.id,
        message_id=update.message.message_id
    )

    info = await context.bot.send_message(
        ADMIN_ID,
        f"📥 سفارش\n👤 {user.id}\n📦 {plan}\n\nریپلای کن برای ارسال"
    )

    pending_orders[info.message_id] = user.id

    await update.message.reply_text("⏳ منتظر تایید ادمین")

# ----------------- ADMIN SEND -----------------
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        return

    msg_id = update.message.reply_to_message.message_id

    if msg_id in pending_orders:
        user_id = pending_orders[msg_id]
        plan = pending_orders.get(user_id)

        if configs[plan]:
            cfg = configs[plan].pop(0)

            await context.bot.send_message(
                user_id,
                f"✅ کانفیگ:\n`{cfg}`",
                parse_mode="Markdown"
            )

            await update.message.reply_text("ارسال شد")
        else:
            await update.message.reply_text("❌ موجود نیست")

        del pending_orders[msg_id]

# ----------------- MAIN -----------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("open", open_shop))
    app.add_handler(CommandHandler("close", close_shop))
    app.add_handler(CommandHandler("stockfull", stock_full))
    app.add_handler(CommandHandler("remove", remove_config))

    app.add_handler(CommandHandler("add1", add_config))
    app.add_handler(CommandHandler("add2", add_config))
    app.add_handler(CommandHandler("add3", add_config))
    app.add_handler(CommandHandler("add4", add_config))
    app.add_handler(CommandHandler("add5", add_config))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, admin_reply))

    print("Bot Running...")
    app.run_polling()
