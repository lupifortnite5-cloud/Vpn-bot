import os
import json
import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ==================================
# تنظیمات اصلی
# ==================================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

CARD_NUMBER = "6221061258771031"
SUPPORT_ID = "@your_support_id"

DATA_FILE = "data.json"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ==================================
# قیمت ها
# ==================================
prices = {
    "1 گیگ": 450,
    "2 گیگ": 820,
    "3 گیگ": 1150,
    "4 گیگ": 1450,
    "5 گیگ": 1750,
}

plans = list(prices.keys())

# ==================================
# سفارش های در انتظار
# ==================================
pending_orders = {}

# ==================================
# فایل دیتا
# ==================================
def default_data():
    return {
        "shop_open": True,
        "configs": {
            "1 گیگ": [],
            "2 گیگ": [],
            "3 گیگ": [],
            "4 گیگ": [],
            "5 گیگ": [],
        }
    }


def load_data():
    if not os.path.exists(DATA_FILE):
        return default_data()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "shop_open" not in data:
            data["shop_open"] = True

        if "configs" not in data:
            data["configs"] = {}

        for p in plans:
            if p not in data["configs"]:
                data["configs"][p] = []

        return data

    except:
        return default_data()


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


data = load_data()

# ==================================
# کیبورد اصلی
# ==================================
def main_menu(user_id):
    keyboard = [
        ["🛒 خرید VPN"],
        ["📦 پلن‌ها", "📊 موجودی"],
        ["📞 پشتیبانی"]
    ]

    if user_id == ADMIN_ID:
        keyboard.append(["🛠 پنل ادمین"])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ==================================
# استارت
# ==================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋 خوش اومدی",
        reply_markup=main_menu(update.effective_user.id)
    )


# ==================================
# هندل متن
# ==================================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text == "🛒 خرید VPN":
        if not data["shop_open"]:
            await update.message.reply_text("🔴 فروش بسته است")
            return

        keyboard = [[p] for p in plans]
        keyboard.append(["🔙 بازگشت"])

        await update.message.reply_text(
            "پلن مورد نظر را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    if text == "🔙 بازگشت":
        await update.message.reply_text(
            "برگشتید به منوی اصلی",
            reply_markup=main_menu(user_id)
        )
        return

    if text in plans:
        if not data["shop_open"]:
            await update.message.reply_text("🔴 فروش بسته است")
            return

        stock = len(data["configs"][text])

        if stock <= 0:
            await update.message.reply_text("❌ موجودی این پلن تمام شده")
            return

        pending_orders[user_id] = {"plan": text}

        await update.message.reply_text(
            f"📦 پلن انتخابی: {text}\n"
            f"💰 مبلغ: {prices[text]} هزار تومان\n\n"
            f"💳 شماره کارت:\n{CARD_NUMBER}\n\n"
            f"📸 پس از پرداخت، رسید را ارسال کنید."
        )
        return

    if text == "📦 پلن‌ها":
        msg = "📦 تعرفه ها:\n\n"
        for p in plans:
            msg += f"{p}: {prices[p]} هزار تومان\n"

        await update.message.reply_text(msg)
        return

    if text == "📊 موجودی":
        msg = "📊 موجودی فعلی:\n\n"
        for p in plans:
            msg += f"{p}: {len(data['configs'][p])} عدد\n"

        await update.message.reply_text(msg)
        return

    if text == "📞 پشتیبانی":
        await update.message.reply_text(SUPPORT_ID)
        return

    if text == "🛠 پنل ادمین" and user_id == ADMIN_ID:
        status = "🟢 باز" if data["shop_open"] else "🔴 بسته"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 استاک کامل", callback_data="stock")],
            [InlineKeyboardButton("🟢 باز کردن فروش", callback_data="open")],
            [InlineKeyboardButton("🔴 بستن فروش", callback_data="close")],
        ])

        await update.message.reply_text(
            f"پنل ادمین\nوضعیت فروش: {status}",
            reply_markup=keyboard
        )
        return


# ==================================
# رسید پرداخت
# ==================================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in pending_orders:
        await update.message.reply_text("❌ ابتدا خرید را شروع کنید")
        return

    plan = pending_orders[user_id]["plan"]

    if not data["shop_open"]:
        await update.message.reply_text("🔴 فروش بسته است")
        return

    if len(data["configs"][plan]) <= 0:
        await update.message.reply_text("❌ موجودی این پلن تمام شده")
        return

    username = update.effective_user.username
    show_user = f"@{username}" if username else str(user_id)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تایید", callback_data=f"ok|{user_id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"no|{user_id}")
        ]
    ])

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=(
            f"📥 سفارش جدید\n"
            f"👤 کاربر: {show_user}\n"
            f"🆔 ID: {user_id}\n"
            f"📦 پلن: {plan}"
        ),
        reply_markup=keyboard
    )

    await update.message.reply_text("⏳ رسید ارسال شد، منتظر تایید باشید.")


# ==================================
# دکمه های ادمین
# ==================================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    data_cb = query.data

    if data_cb.startswith("ok|"):
        user_id = int(data_cb.split("|")[1])

        if user_id not in pending_orders:
            await query.message.edit_caption("❌ سفارش پیدا نشد")
            return

        plan = pending_orders[user_id]["plan"]

        if len(data["configs"][plan]) <= 0:
            await query.message.edit_caption("❌ موجودی تمام شد")
            return

        item = data["configs"][plan].pop(0)
        save_data()

        if isinstance(item, dict):
            config_link = item.get("config", "")
            sub_link = item.get("sub", "")
        else:
            config_link = item
            sub_link = ""

        msg = (
            f"✅ خرید شما تایید شد\n\n"
            f"📦 پلن: {plan}\n\n"
            f"🔗 کانفیگ:\n"
            f"`{config_link}`"
        )

        if sub_link:
            msg += f"\n\n🌐 لینک ساب:\n{sub_link}"

        msg += (
            "\n\n📊 برای مشاهده حجم باقی‌مانده، "
            "لینک ساب را داخل برنامه وارد کنید."
        )

        await context.bot.send_message(
            user_id,
            msg,
            parse_mode="Markdown"
        )

        del pending_orders[user_id]

        await query.message.edit_caption("✅ ارسال شد")
        return

    if data_cb.startswith("no|"):
        user_id = int(data_cb.split("|")[1])

        pending_orders.pop(user_id, None)

        await context.bot.send_message(
            user_id,
            "❌ سفارش رد شد، با پشتیبانی تماس بگیرید."
        )

        await query.message.edit_caption("🚫 رد شد")
        return

    if data_cb == "stock":
        msg = "📦 استاک کامل:\n\n"

        for p in plans:
            msg += f"--- {p} ---\n"

            for i, item in enumerate(data["configs"][p], start=1):
                if isinstance(item, dict):
                    cfg = item["config"]
                else:
                    cfg = item

                msg += f"{i}. {cfg}\n"

            msg += "\n"

        await query.message.edit_text(msg[:4000])
        return

    if data_cb == "close":
        data["shop_open"] = False
        save_data()

        await query.message.edit_text("🔴 فروش بسته شد")
        return

    if data_cb == "open":
        data["shop_open"] = True
        save_data()

        await query.message.edit_text("🟢 فروش باز شد")
        return


# ==================================
# افزودن تکی
# /add 1 گیگ vless://... | https://sub...
# ==================================
async def add_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    raw = update.message.text.replace("/add", "", 1).strip()

    selected_plan = None

    for p in plans:
        if raw.startswith(p):
            selected_plan = p
            raw = raw.replace(p, "", 1).strip()
            break

    if not selected_plan:
        await update.message.reply_text("❌ پلن اشتباه است")
        return

    if "|" in raw:
        config_link, sub_link = raw.split("|", 1)
        config_link = config_link.strip()
        sub_link = sub_link.strip()
    else:
        config_link = raw.strip()
        sub_link = ""

    if not config_link.startswith("vless://"):
        await update.message.reply_text("❌ کانفیگ نامعتبر است")
        return

    item = {
        "config": config_link,
        "sub": sub_link
    }

    data["configs"][selected_plan].append(item)
    save_data()

    await update.message.reply_text(
        f"✅ اضافه شد\n"
        f"📦 {selected_plan}\n"
        f"📊 موجودی: {len(data['configs'][selected_plan])}"
    )


# ==================================
# افزودن گروهی
# ==================================
async def add_bulk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    lines = update.message.text.split("\n")

    if len(lines) < 2:
        await update.message.reply_text("❌ فرمت اشتباه است")
        return

    first_line = lines[0].replace("/addbulk", "", 1).strip()

    selected_plan = None

    for p in plans:
        if first_line == p:
            selected_plan = p
            break

    if not selected_plan:
        await update.message.reply_text("❌ پلن اشتباه است")
        return

    count = 0

    for line in lines[1:]:
        line = line.strip()

        if not line:
            continue

        if "|" in line:
            config_link, sub_link = line.split("|", 1)
            config_link = config_link.strip()
            sub_link = sub_link.strip()
        else:
            config_link = line
            sub_link = ""

        if not config_link.startswith("vless://"):
            continue

        item = {
            "config": config_link,
            "sub": sub_link
        }

        data["configs"][selected_plan].append(item)
        count += 1

    save_data()

    await update.message.reply_text(
        f"✅ تعداد {count} کانفیگ به {selected_plan} اضافه شد."
    )


# ==================================
# اجرای ربات
# ==================================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_config))
    app.add_handler(CommandHandler("addbulk", add_bulk))

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.add_handler(CallbackQueryHandler(handle_callback))

    print("Bot is Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
