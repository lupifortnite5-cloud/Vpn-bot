import os
import json
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

CARD = "6221061258771031"
SUPPORT = "@your_support_id"

logging.basicConfig(level=logging.INFO)

FILE = "data.json"

def load():
    if not os.path.exists(FILE):
        return {"configs": {}, "shop_open": True}
    return json.load(open(FILE, "r", encoding="utf-8"))

def save(data):
    json.dump(data, open(FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

data = load()

prices = {
    "1 گیگ": 450,
    "2 گیگ": 820,
    "3 گیگ": 1150,
    "4 گیگ": 1450,
    "5 گیگ": 1750
}

plans = list(prices.keys())
pending = {}

def main_kb(uid):
    kb = [
        ["🛒 خرید VPN"],
        ["📦 پلن‌ها", "📊 موجودی"],
        ["📞 پشتیبانی"]
    ]
    if uid == ADMIN_ID:
        kb.append(["🛠 پنل ادمین"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text("سلام 👋", reply_markup=main_kb(update.effective_user.id))

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.effective_user.id
    t = update.message.text.strip()

    if t == "🛒 خرید VPN":
        if not data["shop_open"]:
            await update.message.reply_text("🔴 فروش بسته است")
            return

        kb = [[p] for p in plans]
        kb.append(["🔙 بازگشت"])
        await update.message.reply_text("پلن رو انتخاب کن:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
        return

    if t == "🔙 بازگشت":
        await update.message.reply_text("برگشتی به منو", reply_markup=main_kb(uid))
        return

    if t in plans:
        if not data["shop_open"]:
            await update.message.reply_text("🔴 فروش بسته است")
            return

        stock = len(data["configs"].get(t, []))
        if stock == 0:
            await update.message.reply_text("❌ موجودی نداره")
            return

        pending[uid] = {"plan": t}

        await update.message.reply_text(
            f"📦 {t}\n💰 {prices[t]} هزار تومان\n\n💳 `{CARD}`\n\n📸 رسید رو بفرست",
            parse_mode="Markdown"
        )
        return

    if t == "📦 پلن‌ها":
        msg = "📦 لیست قیمت:\n\n"
        for p, price in prices.items():
            msg += f"{p}: {price} هزار تومان\n"
        await update.message.reply_text(msg)
        return

    if t == "📊 موجودی":
        msg = "📊 موجودی:\n\n"
        for p in plans:
            msg += f"{p}: {len(data['configs'].get(p, []))} عدد\n"
        await update.message.reply_text(msg)
        return

    if t == "📞 پشتیبانی":
        await update.message.reply_text(SUPPORT)
        return

    if t == "🛠 پنل ادمین" and uid == ADMIN_ID:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 استاک کامل", callback_data="fullstock")],
            [InlineKeyboardButton("🔴 بستن فروش", callback_data="close")],
            [InlineKeyboardButton("🟢 باز کردن فروش", callback_data="open")]
        ])
        await update.message.reply_text("پنل ادمین:", reply_markup=kb)
        return

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.effective_user.id

    if uid not in pending:
        await update.message.reply_text("❌ اول خرید کن")
        return

    plan = pending[uid]["plan"]

    if not data["shop_open"]:
        await update.message.reply_text("🔴 فروش بسته است")
        return

    if len(data["configs"].get(plan, [])) == 0:
        await update.message.reply_text("❌ موجودی تموم شده")
        return

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تایید", callback_data=f"ok|{uid}"),
            InlineKeyboardButton("❌ رد", callback_data=f"no|{uid}")
        ]
    ])

    await context.bot.send_photo(
        ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=f"📥 سفارش\n👤 {uid}\n📦 {plan}",
        reply_markup=kb
    )

    await update.message.reply_text("⏳ منتظر تایید ادمین باش")

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return

    await q.answer()

    if q.from_user.id != ADMIN_ID:
        return

    data_cb = q.data

    if data_cb.startswith("ok|"):
        user_id = int(data_cb.split("|")[1])

        if user_id not in pending:
            return

        plan = pending[user_id]["plan"]

        if len(data["configs"].get(plan, [])) == 0:
            await q.message.edit_caption("❌ موجودی تموم شد")
            return

        config = data["configs"][plan].pop(0)
        save(data)

        await context.bot.send_message(
            user_id,
            f"✅ خرید تایید شد\n\n📦 {plan}\n\n`{config}`",
            parse_mode="Markdown"
        )

        del pending[user_id]
        await q.message.edit_caption("✅ ارسال شد")

    elif data_cb.startswith("no|"):
        user_id = int(data_cb.split("|")[1])
        pending.pop(user_id, None)
        await context.bot.send_message(user_id, "❌ رد شد")
        await q.message.edit_caption("🚫 رد شد")

    elif data_cb == "fullstock":
        msg = "📦 استاک کامل:\n\n"
        for p in plans:
            msg += f"{p}:\n"
            for i, cfg in enumerate(data["configs"].get(p, [])):
                msg += f"{i}: {cfg}\n"
            msg += "\n"
        await q.message.edit_text(msg)

    elif data_cb == "close":
        data["shop_open"] = False
        save(data)
        await q.message.edit_text("🔴 بسته شد")

    elif data_cb == "open":
        data["shop_open"] = True
        save(data)
        await q.message.edit_text("🟢 باز شد")

# ✅ ADD بدون کرش
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if update.effective_user.id != ADMIN_ID:
        return

    try:
        text = update.message.text.replace("/add", "", 1).strip()

        if not text.startswith("vless://"):
            await update.message.reply_text("❌ کانفیگ نامعتبره")
            return

        lower = text.lower()

        if "#1g" in lower or "1گیگ" in lower:
            plan = "1 گیگ"
        elif "#2g" in lower or "2گیگ" in lower:
            plan = "2 گیگ"
        elif "#3g" in lower or "3گیگ" in lower:
            plan = "3 گیگ"
        elif "#4g" in lower or "4گیگ" in lower:
            plan = "4 گیگ"
        elif "#5g" in lower or "5گیگ" in lower:
            plan = "5 گیگ"
        else:
            await update.message.reply_text("❌ حجم مشخص نیست (#3G بذار)")
            return

        data["configs"].setdefault(plan, [])
        data["configs"][plan].append(text)
        save(data)

        await update.message.reply_text(
            f"✅ اضافه شد\n📦 {plan}\n📊 موجودی: {len(data['configs'][plan])}"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))
    app.add_handler(MessageHandler(filters.PHOTO, photo))
    app.add_handler(CallbackQueryHandler(callback))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
