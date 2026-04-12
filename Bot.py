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
sales = []


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


def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 استاک", callback_data="stock")],
        [InlineKeyboardButton("➕ افزودن کانفیگ", callback_data="add_help")],
        [InlineKeyboardButton("🗑 حذف کانفیگ", callback_data="remove_help")],
        [InlineKeyboardButton("📊 آمار", callback_data="stats")],
        [InlineKeyboardButton("💾 بکاپ", callback_data="backup")],
        [InlineKeyboardButton("🏠 بستن پنل", callback_data="close")]
    ])


# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    await update.message.reply_text("سلام 👋", reply_markup=main_keyboard(uid))


# ---------- ADMIN ADD ----------
async def add_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    cmd = update.message.text.split()[0]
    config = update.message.text.replace(cmd, "").strip()

    map_cmd = {
        "/add1": plan_list[0],
        "/add2": plan_list[1],
        "/add3": plan_list[2],
        "/add4": plan_list[3],
        "/add5": plan_list[4],
    }

    plan = map_cmd.get(cmd)

    if not plan or not config:
        await update.message.reply_text("❌ /add1 تا /add5 + کانفیگ")
        return

    configs[plan].append(config)

    await update.message.reply_text(f"✅ اضافه شد\n{plan}\n📦 تعداد: {len(configs[plan])}")


# ---------- TEXT ----------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.message.from_user.id

    # support
    if text == "📞 پشتیبانی":
        await update.message.reply_text(SUPPORT_ID)
        return

    # back home
    if text == "🏠 منو اصلی":
        await update.message.reply_text("🏠 منو اصلی", reply_markup=main_keyboard(uid))
        return

    # plans
    if text == "📦 پلن‌ها":
        msg = "📦 پلن‌ها:\n\n"
        for p, price in plans.items():
            msg += f"{p}: {price} تومان\n"
        await update.message.reply_text(msg)
        return

    # buy
    if text == "🛒 خرید VPN":
        kb = [[p] for p in plans]
        kb.append(["✔ نهایی‌سازی خرید"])
        kb.append(["🏠 منو اصلی"])

        await update.message.reply_text(
            "پلن رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return

    # add cart
    if text in plans:
        cart.setdefault(uid, {})
        cart[uid][text] = cart[uid].get(text, 0) + 1

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑 حذف از سبد", callback_data=f"del|{text}")],
            [InlineKeyboardButton("🏠 منو اصلی", callback_data="home")]
        ])

        await update.message.reply_text(
            f"➕ اضافه شد:\n{text}\n📦 تعداد: {cart[uid][text]}",
            reply_markup=kb
        )
        return

    # cart
    if text == "🗑 سبد خرید":
        if uid not in cart or not cart[uid]:
            await update.message.reply_text("🛒 سبد خالیه")
            return

        msg = "🛒 سبد خرید:\n\n"
        for p, c in cart[uid].items():
            msg += f"{p} × {c}\n"

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✔ نهایی‌سازی خرید", callback_data="checkout")],
            [InlineKeyboardButton("🏠 منو اصلی", callback_data="home")]
        ])

        await update.message.reply_text(msg, reply_markup=kb)
        return

    # admin panel open
    if text == "🛠 پنل ادمین" and uid == ADMIN_ID:
        await update.message.reply_text("🛠 پنل ادمین", reply_markup=admin_keyboard())
        return

    await update.message.reply_text("از منو استفاده کن", reply_markup=main_keyboard(uid))


# ---------- CALLBACK ----------
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    data = q.data

    # home
    if data == "home":
        await q.message.edit_text("🏠 منو اصلی")
        return

    # close panel
    if data == "close":
        await q.message.edit_text("بسته شد")
        return

    # stock
    if data == "stock":
        msg = "📦 استاک:\n\n"
        for p, lst in configs.items():
            msg += f"{p}: {len(lst)}\n"
        await q.message.edit_text(msg)
        return

    # stats
    if data == "stats":
        await q.message.edit_text(
            f"📊 آمار\nفروش: {len(sales)}\nکاربران: {len(cart)}"
        )
        return

    # backup
    if data == "backup":
        await context.bot.send_document(ADMIN_ID, open("configs.json", "rb"))
        await q.message.edit_text("💾 بکاپ ارسال شد")
        return

    # help add
    if data == "add_help":
        await q.message.edit_text("برای افزودن:\n/add1 متن کانفیگ")
        return

    # help remove
    if data == "remove_help":
        await q.message.edit_text("برای حذف:\n/remove index plan_index")
        return

    # delete cart item
    if data.startswith("del|"):
        plan = data.split("|")[1]
        if uid in cart and plan in cart[uid]:
            del cart[uid][plan]
        await q.message.edit_text("🗑 حذف شد")
        return

    # checkout
    if data == "checkout":
        if uid not in cart or not cart[uid]:
            await q.message.edit_text("سبد خالیه")
            return

        # STOCK CHECK واقعی
        for plan, count in cart[uid].items():
            if len(configs.get(plan, [])) < count:
                await q.message.edit_text(
                    f"❌ موجودی کم است:\n{plan}\n"
                    f"درخواست: {count}\n"
                    f"موجود: {len(configs.get(plan, []))}"
                )
                return

        total = 0
        msg = ""

        for plan, count in cart[uid].items():
            total += plans[plan] * count
            msg += f"{plan} × {count}\n"

        await q.message.edit_text(
            f"💳 پرداخت:\n{CARD_NUMBER}\n{CARD_OWNER}\n\n"
            f"{msg}\n💰 {total} تومان\n\n📸 رسید بفرست"
        )


# ---------- REMOVE ----------
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    try:
        i = int(context.args[0])
        p = plan_list[int(context.args[1])]

        removed = configs[p].pop(i)
        await update.message.reply_text(f"🗑 حذف شد:\n{removed}")

    except:
        await update.message.reply_text("❌ /remove index plan")


# ---------- APP ----------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add1", add_config))
app.add_handler(CommandHandler("add2", add_config))
app.add_handler(CommandHandler("add3", add_config))
app.add_handler(CommandHandler("add4", add_config))
app.add_handler(CommandHandler("add5", add_config))
app.add_handler(CommandHandler("remove", remove))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(callback))

app.run_polling()
