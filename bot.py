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

TOKEN = os.environ.get(“TELEGRAM_BOT_TOKEN”)
ADMIN_ID = int(os.environ.get(“ADMIN_ID”, “0”))

SUPPORT_ID = “@your_support_id”

plans = {
“1 گیگ - یک ماهه”: 400,
“2 گیگ - یک ماهه”: 800,
“3 گیگ - یک ماهه”: 1200,
“4 گیگ - یک ماهه”: 1600,
“5 گیگ - یک ماهه”: 2000,
}

plan_list = list(plans.keys())

CARD_NUMBER = “6221061258771031”
CARD_OWNER = “ایروانی”

cart = {}
pending_orders = {}
configs = {p: [] for p in plans}
sales = []

# ——— SHOP STATUS ———

state = {“shop_open”: True}  # dict تا در همه handler ها درست کار کنه

# ––––– KEYBOARD –––––

def main_keyboard(uid):
kb = [
[“🛒 خرید VPN”],
[“📦 پلن‌ها”],
[“🗑 سبد خرید”],
[“📞 پشتیبانی”],
[“🏠 منو اصلی”]
]
if uid == ADMIN_ID:
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
[InlineKeyboardButton(“🏠 بستن پنل”, callback_data=“close”)]
])

# ––––– START –––––

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
uid = update.message.from_user.id
await update.message.reply_text(“سلام 👋 به ربات VPN خوش اومدی!”, reply_markup=main_keyboard(uid))

# ––––– OPEN / CLOSE SHOP (command) –––––

async def open_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.message.from_user.id != ADMIN_ID:
return
state[“shop_open”] = True
await update.message.reply_text(“🟢 فروشگاه باز شد.\nکامند: /shopopen”)

async def close_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.message.from_user.id != ADMIN_ID:
return
state[“shop_open”] = False
await update.message.reply_text(“🔴 فروشگاه بسته شد.\nکامند: /shopclose”)

# ––––– ADMIN ADD CONFIG –––––

async def add_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.message.from_user.id != ADMIN_ID:
return

```
parts = update.message.text.split(None, 1)
cmd = parts[0]

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
    f"✅ کانفیگ اضافه شد\n📌 پلن: {plan}\n📦 موجودی: {len(configs[plan])}"
)
```

# ––––– REMOVE CONFIG –––––

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.message.from_user.id != ADMIN_ID:
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
            f"❌ ایندکس اشتباه.\nموجودی پلن: {len(configs[p])} عدد (0 تا {len(configs[p])-1})"
        )
        return

    removed = configs[p].pop(i)
    await update.message.reply_text(f"🗑 حذف شد:\n{removed}")

except (ValueError, IndexError):
    await update.message.reply_text("❌ فرمت:\n/remove <index> <plan_index 0-4>")
```

# ––––– TEXT HANDLER –––––

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
text = update.message.text
uid = update.message.from_user.id

```
if text == "📞 پشتیبانی":
    await update.message.reply_text(f"برای پشتیبانی با {SUPPORT_ID} تماس بگیر.")
    return

if text == "🏠 منو اصلی":
    await update.message.reply_text("🏠 منو اصلی", reply_markup=main_keyboard(uid))
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
            "🔴 فروشگاه در حال حاضر بسته است.\nلطفاً بعداً مراجعه کنید یا با پشتیبانی تماس بگیرید."
        )
        return

    kb = [[p] for p in plans]
    kb.append(["✔ نهایی‌سازی خرید"])
    kb.append(["🏠 منو اصلی"])
    await update.message.reply_text(
        "پلن مورد نظرت رو انتخاب کن:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )
    return

if text in plans:
    if not state["shop_open"]:
        await update.message.reply_text("🔴 فروشگاه بسته است.")
        return

    stock = len(configs.get(text, []))

    if stock == 0:
        await update.message.reply_text("❌ متأسفانه این پلن در حال حاضر موجود نیست.")
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
        [InlineKeyboardButton("✔ نهایی‌سازی", callback_data="checkout")]
    ])

    if uid == ADMIN_ID:
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
        [InlineKeyboardButton("🏠 منو اصلی", callback_data="home")]
    ])
    await update.message.reply_text(msg, reply_markup=kb)
    return

if text == "🛠 پنل ادمین" and uid == ADMIN_ID:
    status = "🟢 باز" if state["shop_open"] else "🔴 بسته"
    await update.message.reply_text(
        f"🛠 پنل ادمین\nوضعیت فروشگاه: {status}",
        reply_markup=admin_keyboard()
    )
    return

await update.message.reply_text("از منو استفاده کن 👇", reply_markup=main_keyboard(uid))
```

# ––––– PHOTO HANDLER (receipt) –––––

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
uid = update.message.from_user.id

```
if uid not in cart or not cart[uid]:
    await update.message.reply_text("❌ سبد خرید شما خالی است. ابتدا خرید کنید.")
    return

# ذخیره سفارش pending
pending_orders[uid] = {
    "cart": cart[uid].copy(),
    "photo_id": update.message.photo[-1].file_id,
    "user": update.message.from_user.username or str(uid)
}

# اطلاع به ادمین
msg_admin = f"📬 رسید جدید از @{pending_orders[uid]['user']}:\n\n"
for p, c in cart[uid].items():
    msg_admin += f"• {p} × {c}\n"

kb_admin = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("✅ تایید و ارسال کانفیگ", callback_data=f"approve|{uid}"),
        InlineKeyboardButton("❌ رد", callback_data=f"reject|{uid}")
    ]
])

await context.bot.send_photo(
    ADMIN_ID,
    photo=update.message.photo[-1].file_id,
    caption=msg_admin,
    reply_markup=kb_admin
)

await update.message.reply_text(
    "✅ رسید دریافت شد!\nمنتظر تایید ادمین باش. معمولاً تا چند دقیقه کانفیگ ارسال می‌شه."
)
```

# ––––– CALLBACK –––––

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
q = update.callback_query
await q.answer()

```
uid = q.from_user.id
data = q.data

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
    msg = "📦 موجودی:\n\n"
    for p, lst in configs.items():
        msg += f"• {p}: {len(lst)} عدد\n"
    await q.message.edit_text(msg)
    return

if data == "stats":
    await q.message.edit_text(
        f"📊 آمار فروشگاه\n"
        f"✅ فروش کل: {len(sales)} سفارش\n"
        f"👤 کاربران دارای سبد: {len(cart)}\n"
        f"⏳ سفارشات در انتظار: {len(pending_orders)}"
    )
    return

if data == "backup":
    try:
        backup_data = {
            "configs": {k: v for k, v in configs.items()},
            "sales": sales
        }
        backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)
        with open("/tmp/configs_backup.json", "w", encoding="utf-8") as f:
            f.write(backup_json)
        with open("/tmp/configs_backup.json", "rb") as f:
            await context.bot.send_document(
                ADMIN_ID,
                document=f,
                filename="backup.json"
            )
        await q.message.edit_text("💾 بکاپ ارسال شد.")
    except Exception as e:
        await q.message.edit_text(f"❌ خطا در بکاپ:\n{e}")
    return

if data == "add_help":
    msg = (
        "➕ برای افزودن کانفیگ:\n\n"
        "/add1 <کانفیگ>  ← پلن 1\n"
        "/add2 <کانفیگ>  ← پلن 2\n"
        "/add3 <کانفیگ>  ← پلن 3\n"
        "/add4 <کانفیگ>  ← پلن 4\n"
        "/add5 <کانفیگ>  ← پلن 5"
    )
    await q.message.edit_text(msg)
    return

if data == "remove_help":
    msg = (
        "🗑 برای حذف کانفیگ:\n\n"
        "/remove <index> <plan_index>\n\n"
        "مثال: /remove 0 2\n"
        "(حذف اولین کانفیگ از پلن 3)\n\n"
        "ایندکس پلن‌ها:\n"
    )
    for i, p in enumerate(plan_list):
        msg += f"{i} = {p}\n"
    await q.message.edit_text(msg)
    return

if data == "toggle_shop":
    if uid != ADMIN_ID:
        return
    state["shop_open"] = not state["shop_open"]
    status = "🟢 باز شد" if state["shop_open"] else "🔴 بسته شد"
    await q.message.edit_text(
        f"✅ وضعیت فروشگاه: {status}",
        reply_markup=admin_keyboard()
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

    # بررسی موجودی (بدون نمایش عدد به مشتری)
    for plan, count in cart[uid].items():
        if len(configs.get(plan, [])) < count:
            await q.message.edit_text(
                f"❌ متأسفانه پلن «{plan}» موجود نیست.\nبرای اطلاعات بیشتر با پشتیبانی تماس بگیر."
            )
            return

    total = 0
    msg = "🧾 خلاصه سفارش:\n\n"
    for plan, count in cart[uid].items():
        msg += f"• {plan} × {count} = {plans[plan] * count} تومان\n"
        total += plans[plan] * count

    await q.message.edit_text(
        f"{msg}\n"
        f"💰 مبلغ کل: {total} تومان\n\n"
        f"💳 کارت: {CARD_NUMBER}\n"
        f"👤 به نام: {CARD_OWNER}\n\n"
        f"📸 بعد از پرداخت، رسید را به همین چت ارسال کن."
    )
    return

# تایید سفارش توسط ادمین
if data.startswith("approve|"):
    if uid != ADMIN_ID:
        return

    target_uid = int(data.split("|")[1])

    if target_uid not in pending_orders:
        await q.message.edit_caption("❌ سفارش یافت نشد یا قبلاً پردازش شده.")
        return

    order = pending_orders[target_uid]
    configs_to_send = []

    # بررسی نهایی موجودی
    for plan, count in order["cart"].items():
        if len(configs.get(plan, [])) < count:
            await q.message.edit_caption(
                f"❌ موجودی ناکافی برای {plan}!\nموجود: {len(configs.get(plan, []))}, درخواست: {count}"
            )
            return
        for _ in range(count):
            configs_to_send.append((plan, configs[plan].pop(0)))

    # ارسال کانفیگ‌ها به کاربر
    msg_user = "🎉 خریدت تایید شد! کانفیگ‌هات:\n\n"
    for plan, cfg in configs_to_send:
        msg_user += f"📌 {plan}:\n<code>{cfg}</code>\n\n"

    try:
        await context.bot.send_message(
            target_uid,
            msg_user,
            parse_mode="HTML"
        )
    except Exception as e:
        await q.message.edit_caption(f"❌ خطا در ارسال به کاربر: {e}")
        # برگردوندن کانفیگ‌ها
        for plan, cfg in configs_to_send:
            configs[plan].insert(0, cfg)
        return

    # ثبت فروش
    sales.append({"uid": target_uid, "order": order["cart"]})

    # پاک کردن سبد و سفارش pending
    cart.pop(target_uid, None)
    del pending_orders[target_uid]

    await q.message.edit_caption(f"✅ سفارش کاربر {order['user']} تایید و ارسال شد.")
    return

# رد سفارش توسط ادمین
if data.startswith("reject|"):
    if uid != ADMIN_ID:
        return

    target_uid = int(data.split("|")[1])

    if target_uid in pending_orders:
        del pending_orders[target_uid]

    try:
        await context.bot.send_message(
            target_uid,
            "❌ رسید شما توسط ادمین رد شد.\nدر صورت مشکل با پشتیبانی تماس بگیر."
        )
    except:
        pass

    await q.message.edit_caption("🚫 سفارش رد شد.")
    return
```

# ––––– APP –––––

def main():
app = ApplicationBuilder().token(TOKEN).build()

```
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("shopopen", open_shop))
app.add_handler(CommandHandler("shopclose", close_shop))
app.add_handler(CommandHandler("add1", add_config))
app.add_handler(CommandHandler("add2", add_config))
app.add_handler(CommandHandler("add3", add_config))
app.add_handler(CommandHandler("add4", add_config))
app.add_handler(CommandHandler("add5", add_config))
app.add_handler(CommandHandler("remove", remove))

app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(callback))

app.run_polling(drop_pending_updates=True)
```

if **name** == “**main**”:
main()
