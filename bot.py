import os
import json
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
ApplicationBuilder,
CommandHandler,
MessageHandler,
CallbackQueryHandler,
ContextTypes,
filters,
)

# ––––– LOGGING –––––

logging.basicConfig(
format=”%(asctime)s - %(name)s - %(levelname)s - %(message)s”,
level=logging.INFO,
)
logger = logging.getLogger(**name**)

# ––––– CONFIG –––––

SUPPORT_ID = “@your_support_id”
CARD_NUMBER = “6221061258771031”
CARD_OWNER = “ایروانی”

plans = {
“1 گیگ - یک ماهه”: 400,
“2 گیگ - یک ماهه”: 800,
“3 گیگ - یک ماهه”: 1200,
“4 گیگ - یک ماهه”: 1600,
“5 گیگ - یک ماهه”: 2000,
}
plan_list = list(plans.keys())

# ––––– STATE –––––

cart = {}
pending_orders = {}
configs = {p: [] for p in plans}
sales = []
state = {“shop_open”: True}

# ––––– KEYBOARDS –––––

def main_keyboard(uid: int, admin_id: int):
kb = [
[“🛒 خرید VPN”],
[“📦 پلن‌ها”],
[“🗑 سبد خرید”],
[“📞 پشتیبانی”],
[“🏠 منو اصلی”],
]
if uid == admin_id:
kb.append([“🛠 پنل ادمین”])
return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def admin_keyboard():
status_btn = “🔴 بستن فروشگاه” if state[“shop_open”] else “🟢 باز کردن فروشگاه”
return InlineKeyboardMarkup([
[InlineKeyboardButton(“📦 استاک”, callback_data=“stock”)],
[InlineKeyboardButton(“➕ افزودن کانفیگ”, callback_data=“add_help”)],
[InlineKeyboardButton(“🗑 حذف کانفیگ”, callback_data=“remove_help”)],
[InlineKeyboardButton(“📊 آمار”, callback_data=“stats”)],
[InlineKeyboardButton(“💾 بکاپ”, callback_data=“backup”)],
[InlineKeyboardButton(status_btn, callback_data=“toggle_shop”)],
[InlineKeyboardButton(“🏠 بستن پنل”, callback_data=“close”)],
])

# ––––– HANDLERS –––––

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
uid = update.effective_user.id
admin_id = context.bot_data[“admin_id”]
await update.message.reply_text(
“سلام 👋 به ربات VPN خوش اومدی!”,
reply_markup=main_keyboard(uid, admin_id),
)

async def open_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.effective_user.id != context.bot_data[“admin_id”]:
return
state[“shop_open”] = True
await update.message.reply_text(“🟢 فروشگاه باز شد.”)

async def close_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.effective_user.id != context.bot_data[“admin_id”]:
return
state[“shop_open”] = False
await update.message.reply_text(“🔴 فروشگاه بسته شد.”)

async def add_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
admin_id = context.bot_data[“admin_id”]
if update.effective_user.id != admin_id:
return

```
parts = update.message.text.split(None, 1)
cmd = parts[0].split("@")[0]

if len(parts) < 2 or not parts[1].strip():
    await update.message.reply_text("❌ فرمت اشتباه.\nمثال: /add1 vless://...")
    return

config = parts[1].strip()
map_cmd = {
    "/add1": plan_list[0],
    "/add2": plan_list[1],
    "/add3": plan_list[2],
    "/add4": plan_list[3],
    "/add5": plan_list[4],
}

plan = map_cmd.get(cmd)
if not plan:
    await update.message.reply_text("❌ دستور نامعتبر.")
    return

configs[plan].append(config)
await update.message.reply_text(
    f"✅ کانفیگ اضافه شد\n📌 پلن: {plan}\n📦 موجودی فعلی: {len(configs[plan])}"
)
```

async def remove_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
admin_id = context.bot_data[“admin_id”]
if update.effective_user.id != admin_id:
return

```
if not context.args or len(context.args) < 2:
    await update.message.reply_text("❌ فرمت:\n/remove <index> <plan_index 0-4>")
    return

try:
    i = int(context.args[0])
    p = plan_list[int(context.args[1])]

    if i < 0 or i >= len(configs[p]):
        await update.message.reply_text(
            f"❌ ایندکس اشتباه.\nموجودی این پلن: {len(configs[p])} عدد"
        )
        return

    removed = configs[p].pop(i)
    await update.message.reply_text(f"🗑 حذف شد:\n{removed}")

except (ValueError, IndexError):
    await update.message.reply_text("❌ فرمت:\n/remove <index> <plan_index 0-4>")
```

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
text = update.message.text
uid = update.effective_user.id
admin_id = context.bot_data[“admin_id”]

```
if text == "📞 پشتیبانی":
    await update.message.reply_text(f"برای پشتیبانی با {SUPPORT_ID} تماس بگیر.")
    return

if text == "🏠 منو اصلی":
    await update.message.reply_text(
        "🏠 منو اصلی", reply_markup=main_keyboard(uid, admin_id)
    )
    return

if text == "📦 پلن‌ها":
    msg = "📦 پلن‌های موجود:\n\n"
    for p, price in plans.items():
        msg += f"• {p}: {price} تومان\n"
    await update.message.reply_text(msg)
    return

if text == "🛒 خرید VPN":
    if not state["shop_open"]:
        await update.message.reply_text(
            "🔴 فروشگاه در حال حاضر بسته است.\nبعداً مراجعه کن یا با پشتیبانی تماس بگیر."
        )
        return
    kb = [[p] for p in plans]
    kb.append(["✔ نهایی‌سازی خرید"])
    kb.append(["🏠 منو اصلی"])
    await update.message.reply_text(
        "پلن مورد نظرت رو انتخاب کن:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )
    return

if text in plans:
    if not state["shop_open"]:
        await update.message.reply_text("🔴 فروشگاه بسته است.")
        return

    stock = len(configs.get(text, []))
    if stock == 0:
        await update.message.reply_text("❌ این پلن در حال حاضر موجود نیست.")
        return

    cart.setdefault(uid, {})
    cart[uid][text] = cart[uid].get(text, 0) + 1

    if cart[uid][text] > stock:
        cart[uid][text] -= 1
        await update.message.reply_text("❌ این پلن موجود نیست.")
        return

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑 حذف از سبد", callback_data=f"del|{text}")],
        [InlineKeyboardButton("🛒 ادامه خرید", callback_data="continue_buy")],
        [InlineKeyboardButton("✔ نهایی‌سازی", callback_data="checkout")],
    ])

    if uid == admin_id:
        msg = f"✅ {text} به سبد اضافه شد.\n📦 موجودی: {stock} عدد"
    else:
        msg = f"✅ {text} به سبد اضافه شد."

    await update.message.reply_text(msg, reply_markup=kb)
    return

if text == "🗑 سبد خرید":
    if uid not in cart or not cart[uid]:
        await update.message.reply_text("🛒 سبد خرید شما خالی است.")
        return

    msg = "🛒 سبد خرید:\n\n"
    total = 0
    for p, c in cart[uid].items():
        msg += f"• {p} × {c} = {plans[p] * c} تومان\n"
        total += plans[p] * c
    msg += f"\n💰 مجموع: {total} تومان"

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✔ نهایی‌سازی خرید", callback_data="checkout")],
        [InlineKeyboardButton("🗑 خالی کردن سبد", callback_data="clear_cart")],
        [InlineKeyboardButton("🏠 منو اصلی", callback_data="home")],
    ])
    await update.message.reply_text(msg, reply_markup=kb)
    return

if text == "🛠 پنل ادمین" and uid == admin_id:
    status = "🟢 باز" if state["shop_open"] else "🔴 بسته"
    await update.message.reply_text(
        f"🛠 پنل ادمین\nوضعیت فروشگاه: {status}",
        reply_markup=admin_keyboard(),
    )
    return

await update.message.reply_text(
    "از منو استفاده کن 👇", reply_markup=main_keyboard(uid, admin_id)
)
```

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
uid = update.effective_user.id
admin_id = context.bot_data[“admin_id”]

```
if uid not in cart or not cart[uid]:
    await update.message.reply_text("❌ سبد خرید شما خالی است. ابتدا خرید کنید.")
    return

pending_orders[uid] = {
    "cart": cart[uid].copy(),
    "photo_id": update.message.photo[-1].file_id,
    "user": update.effective_user.username or str(uid),
}

msg_admin = f"📬 رسید جدید از @{pending_orders[uid]['user']}:\n\n"
for p, c in cart[uid].items():
    msg_admin += f"• {p} × {c}\n"

kb_admin = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("✅ تایید و ارسال کانفیگ", callback_data=f"approve|{uid}"),
        InlineKeyboardButton("❌ رد", callback_data=f"reject|{uid}"),
    ]
])

await context.bot.send_photo(
    admin_id,
    photo=update.message.photo[-1].file_id,
    caption=msg_admin,
    reply_markup=kb_admin,
)
await update.message.reply_text(
    "✅ رسید دریافت شد!\nمنتظر تایید ادمین باش. معمولاً تا چند دقیقه کانفیگ ارسال میشه."
)
```

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
q = update.callback_query
await q.answer()
uid = q.from_user.id
admin_id = context.bot_data[“admin_id”]
data = q.data

```
if data == "home":
    await q.message.edit_text("🏠 برگشتی به منو اصلی.")
    return

if data == "close":
    await q.message.edit_text("✔ پنل بسته شد.")
    return

if data == "continue_buy":
    await q.message.edit_text("✅ ادامه بده، پلن بعدی رو انتخاب کن.")
    return

if data == "clear_cart":
    cart.pop(uid, None)
    await q.message.edit_text("🗑 سبد خالی شد.")
    return

if data == "stock":
    if uid != admin_id:
        return
    msg = "📦 موجودی:\n\n"
    for p, lst in configs.items():
        msg += f"• {p}: {len(lst)} عدد\n"
    await q.message.edit_text(msg)
    return

if data == "stats":
    if uid != admin_id:
        return
    await q.message.edit_text(
        f"📊 آمار فروشگاه\n"
        f"✅ فروش کل: {len(sales)} سفارش\n"
        f"👤 کاربران دارای سبد: {len(cart)}\n"
        f"⏳ سفارشات در انتظار: {len(pending_orders)}"
    )
    return

if data == "backup":
    if uid != admin_id:
        return
    try:
        backup_data = {"configs": configs, "sales": sales}
        backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)
        with open("/tmp/backup.json", "w", encoding="utf-8") as f:
            f.write(backup_json)
        with open("/tmp/backup.json", "rb") as f:
            await context.bot.send_document(admin_id, document=f, filename="backup.json")
        await q.message.edit_text("💾 بکاپ ارسال شد.")
    except Exception as e:
        logger.error(f"Backup error: {e}")
        await q.message.edit_text(f"❌ خطا در بکاپ:\n{e}")
    return

if data == "add_help":
    msg = "➕ برای افزودن کانفیگ:\n\n"
    for i, p in enumerate(plan_list, 1):
        msg += f"/add{i} <کانفیگ>  ← {p}\n"
    await q.message.edit_text(msg)
    return

if data == "remove_help":
    msg = "🗑 برای حذف کانفیگ:\n/remove <index> <plan_index>\n\nایندکس پلن‌ها:\n"
    for i, p in enumerate(plan_list):
        msg += f"{i} = {p}\n"
    await q.message.edit_text(msg)
    return

if data == "toggle_shop":
    if uid != admin_id:
        return
    state["shop_open"] = not state["shop_open"]
    status = "🟢 باز شد" if state["shop_open"] else "🔴 بسته شد"
    await q.message.edit_text(
        f"✅ وضعیت فروشگاه: {status}", reply_markup=admin_keyboard()
    )
    return

if data.startswith("del|"):
    plan = data.split("|", 1)[1]
    if uid in cart and plan in cart[uid]:
        del cart[uid][plan]
        if not cart[uid]:
            del cart[uid]
    await q.message.edit_text("🗑 پلن از سبد حذف شد.")
    return

if data == "checkout":
    if uid not in cart or not cart[uid]:
        await q.message.edit_text("🛒 سبد خرید خالی است.")
        return
    if not state["shop_open"]:
        await q.message.edit_text("🔴 فروشگاه بسته است.")
        return
    for plan, count in cart[uid].items():
        if len(configs.get(plan, [])) < count:
            await q.message.edit_text(
                f"❌ پلن «{plan}» موجود نیست.\nبا پشتیبانی تماس بگیر."
            )
            return

    total = 0
    msg = "🧾 خلاصه سفارش:\n\n"
    for plan, count in cart[uid].items():
        msg += f"• {plan} × {count} = {plans[plan] * count} تومان\n"
        total += plans[plan] * count

    await q.message.edit_text(
        f"{msg}\n💰 مبلغ کل: {total} تومان\n\n"
        f"💳 کارت: {CARD_NUMBER}\n"
        f"👤 به نام: {CARD_OWNER}\n\n"
        f"📸 بعد از پرداخت رسید رو به همین چت ارسال کن."
    )
    return

if data.startswith("approve|"):
    if uid != admin_id:
        return
    target_uid = int(data.split("|")[1])
    if target_uid not in pending_orders:
        await q.message.edit_caption("❌ سفارش یافت نشد یا قبلاً پردازش شده.")
        return

    order = pending_orders[target_uid]
    configs_to_send = []

    for plan, count in order["cart"].items():
        if len(configs.get(plan, [])) < count:
            await q.message.edit_caption(f"❌ موجودی ناکافی برای {plan}!")
            return
        for _ in range(count):
            configs_to_send.append((plan, configs[plan].pop(0)))

    msg_user = "🎉 خریدت تایید شد! کانفیگ‌هات:\n\n"
    for plan, cfg in configs_to_send:
        msg_user += f"📌 {plan}:\n<code>{cfg}</code>\n\n"

    try:
        await context.bot.send_message(target_uid, msg_user, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Send config error: {e}")
        await q.message.edit_caption(f"❌ خطا در ارسال به کاربر: {e}")
        for plan, cfg in configs_to_send:
            configs[plan].insert(0, cfg)
        return

    sales.append({"uid": target_uid, "order": order["cart"]})
    cart.pop(target_uid, None)
    del pending_orders[target_uid]
    await q.message.edit_caption(f"✅ سفارش کاربر {order['user']} تایید و ارسال شد.")
    return

if data.startswith("reject|"):
    if uid != admin_id:
        return
    target_uid = int(data.split("|")[1])
    pending_orders.pop(target_uid, None)
    try:
        await context.bot.send_message(
            target_uid,
            "❌ رسید شما توسط ادمین رد شد.\nبا پشتیبانی تماس بگیر."
        )
    except Exception as e:
        logger.error(f"Reject notify error: {e}")
    await q.message.edit_caption("🚫 سفارش رد شد.")
    return
```

# ––––– MAIN –––––

def main():
token = os.environ.get(“TELEGRAM_BOT_TOKEN”)
admin_id_str = os.environ.get(“ADMIN_ID”)

```
if not token:
    logger.error("TELEGRAM_BOT_TOKEN تنظیم نشده!")
    return
if not admin_id_str:
    logger.error("ADMIN_ID تنظیم نشده!")
    return

admin_id = int(admin_id_str)
logger.info(f"Bot starting... Admin ID: {admin_id}")

app = ApplicationBuilder().token(token).build()
app.bot_data["admin_id"] = admin_id

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("shopopen", open_shop))
app.add_handler(CommandHandler("shopclose", close_shop))
app.add_handler(CommandHandler("add1", add_config))
app.add_handler(CommandHandler("add2", add_config))
app.add_handler(CommandHandler("add3", add_config))
app.add_handler(CommandHandler("add4", add_config))
app.add_handler(CommandHandler("add5", add_config))
app.add_handler(CommandHandler("remove", remove_config))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(handle_callback))

logger.info("Bot is running!")
app.run_polling(drop_pending_updates=True)
```

if **name** == “**main**”:
main()
