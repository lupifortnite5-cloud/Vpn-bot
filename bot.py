import os
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

SUPPORT_ID = "@your_support_id"

plans = {
    "1 گیگ - یک ماهه": 400,
    "2 گیگ - یک ماهه": 800,
    "3 گیگ - یک ماهه": 1200,
    "4 گیگ - یک ماهه": 1600,
    "5 گیگ - یک ماهه": 2000,
}

CARD_NUMBER = "6221061258771031"
CARD_OWNER = "ایروانی"

cart = {}
pending_orders = {}

# ---------- KEYBOARD ----------
def main_keyboard(uid):
    kb = [["🛒 خرید VPN"], ["📦 پلن‌ها"], ["🗑 سبد خرید"], ["📞 پشتیبانی"]]

    if uid == ADMIN_ID:
        kb.append(["🛠 پنل ادمین"])

    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    await update.message.reply_text("سلام 👋", reply_markup=main_keyboard(uid))


# ---------- TEXT ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    uid = user.id

    # support
    if text == "📞 پشتیبانی":
        await update.message.reply_text(SUPPORT_ID)
        return

    # plans
    if text == "📦 پلن‌ها":
        msg = "📦 پلن‌ها:\n\n"
        for p, price in plans.items():
            msg += f"{p}: {price} تومان\n"
        await update.message.reply_text(msg)
        return

    # buy menu
    if text == "🛒 خرید VPN":
        kb = [[p] for p in plans]
        kb.append(["✔ نهایی‌سازی خرید"])

        await update.message.reply_text(
            "پلن رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return

    # add to cart
    if text in plans:
        cart.setdefault(uid, {})
        cart[uid][text] = cart[uid].get(text, 0) + 1

        await update.message.reply_text(
            f"➕ اضافه شد:\n{text}\n📦 تعداد: {cart[uid][text]}"
        )
        return

    # show cart
    if text == "🗑 سبد خرید":
        if uid not in cart or not cart[uid]:
            await update.message.reply_text("🛒 سبد خالیه")
            return

        msg = "🛒 سبد خرید:\n\n"
        i = 1

        for plan, count in cart[uid].items():
            msg += f"{i}) {plan} × {count}\n"
            i += 1

        msg += "\nبرای حذف بنویس:\n🗑 شماره آیتم"
        await update.message.reply_text(msg)
        return

    # delete item from cart
    if text.isdigit():
        if uid not in cart or not cart[uid]:
            return

        index = int(text) - 1
        items = list(cart[uid].items())

        if index < 0 or index >= len(items):
            await update.message.reply_text("❌ شماره اشتباهه")
            return

        plan, count = items[index]

        del cart[uid][plan]

        await update.message.reply_text(f"🗑 حذف شد:\n{plan}")
        return

    # checkout
    if text == "✔ نهایی‌سازی خرید":
        if uid not in cart or not cart[uid]:
            await update.message.reply_text("🛒 سبد خالیه")
            return

        # stock check
        for plan in cart[uid]:
            if len(configs.get(plan, [])) == 0:
                await update.message.reply_text(f"❌ موجودی نداریم برای:\n{plan}")
                return

        total = 0
        summary = ""

        for plan, count in cart[uid].items():
            price = plans[plan]
            total += price * count
            summary += f"{plan} × {count}\n"

        await update.message.reply_text(
            "💳 پرداخت:\n"
            f"{CARD_NUMBER}\n"
            f"{CARD_OWNER}\n\n"
            f"🧾 سفارش:\n{summary}\n"
            f"💰 جمع کل: {total} تومان\n\n"
            "📸 رسید رو ارسال کن"
        )
        return

    await update.message.reply_text("از منو استفاده کن", reply_markup=main_keyboard(uid))


# ---------- RECEIPT ----------
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    uid = user.id

    if uid not in cart:
        return

    msg = await context.bot.send_message(
        ADMIN_ID,
        f"📥 سفارش جدید\n👤 {user.first_name}\n🆔 {uid}\n\nریپلای کن"
    )

    pending_orders[msg.message_id] = uid
    await update.message.reply_text("✅ رسید ارسال شد")


# ---------- ADMIN REPLY ----------
async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        return

    mid = update.message.reply_to_message.message_id
    uid = pending_orders.get(mid)

    if not uid:
        return

    cart[uid] = {}

    await context.bot.send_message(
        uid,
        "✅ سفارش تایید شد"
    )

    await update.message.reply_text("ارسال شد")


# ---------- RUN ----------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_media))

app.run_polling()
