import os
import json
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
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

plan_list = list(plans.keys())

CARD_NUMBER = "6221061258771031"
CARD_OWNER = "ایروانی"

cart = {}
pending_orders = {}
configs = {p: [] for p in plans}


# ---------- KEYBOARD ----------
def main_keyboard(uid):
    kb = [
        ["🛒 خرید VPN"],
        ["📦 پلن‌ها"],
        ["🗑 سبد خرید"],
        ["📞 پشتیبانی"],
        ["🏠 منو اصلی"]
    ]

    if uid == ADMIN_ID:
        kb.append(["🛠 پنل ادمین"])

    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    await update.message.reply_text("سلام 👋", reply_markup=main_keyboard(uid))


# ---------- ADMIN QUICK ADD ----------
async def add_quick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    cmd = update.message.text.split()[0]
    config = update.message.text.replace(cmd, "").strip()

    plan_map = {
        "/add1": plan_list[0],
        "/add2": plan_list[1],
        "/add3": plan_list[2],
        "/add4": plan_list[3],
        "/add5": plan_list[4],
    }

    plan = plan_map.get(cmd)

    if not plan or not config:
        await update.message.reply_text("❌ /add1 تا /add5 + کانفیگ")
        return

    configs[plan].append(config)

    await update.message.reply_text(
        f"✅ اضافه شد\n📦 {plan}\n📊 تعداد: {len(configs[plan])}"
    )


# ---------- TEXT ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.message.from_user.id

    if text == "📞 پشتیبانی":
        await update.message.reply_text(SUPPORT_ID)
        return

    if text == "🏠 منو اصلی":
        await update.message.reply_text("🏠 منو اصلی", reply_markup=main_keyboard(uid))
        return

    if text == "📦 پلن‌ها":
        msg = "📦 پلن‌ها:\n\n"
        for p, price in plans.items():
            msg += f"{p}: {price} تومان\n"
        await update.message.reply_text(msg)
        return

    if text == "🛒 خرید VPN":
        kb = [[p] for p in plans]
        kb.append(["✔ نهایی‌سازی خرید"])
        kb.append(["🏠 منو اصلی"])

        await update.message.reply_text(
            "پلن رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return

    if text in plans:
        cart.setdefault(uid, {})
        cart[uid][text] = cart[uid].get(text, 0) + 1

        kb = [
            [InlineKeyboardButton("🗑 حذف از سبد", callback_data=f"del|{text}")],
            [InlineKeyboardButton("🏠 منو اصلی", callback_data="home")]
        ]

        await update.message.reply_text(
            f"➕ اضافه شد:\n{text}\n📦 تعداد: {cart[uid][text]}",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    if text == "🗑 سبد خرید":
        if uid not in cart or not cart[uid]:
            await update.message.reply_text("🛒 سبد خالیه")
            return

        msg = "🛒 سبد خرید:\n\n"
        for p, c in cart[uid].items():
            msg += f"{p} × {c}\n"

        kb = [
            [InlineKeyboardButton("✔ نهایی‌سازی خرید", callback_data="checkout")],
            [InlineKeyboardButton("🏠 منو اصلی", callback_data="home")]
        ]

        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        return


# ---------- CALLBACK ----------
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    data = q.data

    if data == "home":
        await q.message.edit_text("🏠 منو اصلی")
        return

    if data.startswith("del|"):
        plan = data.split("|")[1]

        if uid in cart and plan in cart[uid]:
            del cart[uid][plan]

        await q.message.edit_text("🗑 حذف شد")
        return

    if data == "checkout":
        if uid not in cart or not cart[uid]:
            await q.message.edit_text("🛒 سبد خالیه")
            return

        # ❌ STOCK CHECK واقعی
        for plan, count in cart[uid].items():
            if len(configs.get(plan, [])) < count:
                await q.message.edit_text(
                    f"❌ موجودی کافی نیست:\n{plan}\n"
                    f"درخواست: {count}\n"
                    f"موجود: {len(configs.get(plan, []))}"
                )
                return

        total = 0
        summary = ""

        for plan, count in cart[uid].items():
            total += plans[plan] * count
            summary += f"{plan} × {count}\n"

        await q.message.edit_text(
            "💳 پرداخت:\n"
            f"{CARD_NUMBER}\n"
            f"{CARD_OWNER}\n\n"
            f"🧾 سفارش:\n{summary}\n"
            f"💰 جمع کل: {total} تومان\n\n"
            "📸 رسید رو ارسال کن"
        )
        return


# ---------- ADMIN ADD COMMANDS ----------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(CommandHandler("add1", add_quick))
app.add_handler(CommandHandler("add2", add_quick))
app.add_handler(CommandHandler("add3", add_quick))
app.add_handler(CommandHandler("add4", add_quick))
app.add_handler(CommandHandler("add5", add_quick))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(callback))

app.run_polling()
