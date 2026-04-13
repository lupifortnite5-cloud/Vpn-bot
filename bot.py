import os
import json
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, CallbackQueryHandler,
)

# ----------------- LOGGING -----------------
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ----------------- CONFIG -----------------
SUPPORT_ID = '@your_support_id'
CARD_NUMBER = '6221061258771031'
CARD_OWNER = 'ایروانی'

plans = {
    '1 گیگ - یک ماهه': 400,
    '2 گیگ - یک ماهه': 800,
    '3 گیگ - یک ماهه': 1200,
    '4 گیگ - یک ماهه': 1600,
    '5 گیگ - یک ماهه': 2000,
}

plan_list = list(plans.keys())

state = {'shop_open': True}
pending_orders = {}

configs = {}

# ----------------- FILE -----------------
def load_configs():
    global configs
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            configs = data.get('configs', {})
    except Exception:
        configs = {p: [] for p in plans}


def save_configs():
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump({'configs': configs}, f, ensure_ascii=False, indent=2)


# ----------------- KEYBOARD -----------------
def main_keyboard():
    kb = [
        ['🛒 خرید VPN'],
        ['📦 پلن‌ها'],
        ['📞 پشتیبانی'],
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


# ----------------- START -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('سلام 👋', reply_markup=main_keyboard())


# ----------------- ADMIN STOCK -----------------
async def cmd_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != context.bot_data['admin_id']:
        return

    msg = '📦 موجودی:\n\n'
    for p in plan_list:
        msg += f"{p}: {len(configs.get(p, []))} عدد\n"

    await update.message.reply_text(msg)


# ----------------- OPEN / CLOSE SHOP -----------------
async def cmd_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != context.bot_data['admin_id']:
        return
    state['shop_open'] = True
    await update.message.reply_text('🟢 فروشگاه باز شد.')


async def cmd_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != context.bot_data['admin_id']:
        return
    state['shop_open'] = False
    await update.message.reply_text('🔴 فروشگاه بسته شد.')


# ----------------- ADD CONFIG -----------------
async def add_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != context.bot_data['admin_id']:
        return

    text = update.message.text.split(None, 1)

    if len(text) < 2:
        await update.message.reply_text('❌ مثال: /add1 vless://...')
        return

    cmd = text[0].split('@')[0]
    value = text[1].strip()

    mapping = {
        '/add1': plan_list[0],
        '/add2': plan_list[1],
        '/add3': plan_list[2],
        '/add4': plan_list[3],
        '/add5': plan_list[4],
    }

    plan = mapping.get(cmd)

    if not plan:
        await update.message.reply_text('❌ دستور نامعتبر.')
        return

    configs.setdefault(plan, []).append(value)
    save_configs()

    await update.message.reply_text(f"✅ اضافه شد\n📌 {plan}\n📦 تعداد: {len(configs[plan])}")


# ----------------- REMOVE CONFIG -----------------
async def cmd_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != context.bot_data['admin_id']:
        return

    try:
        idx = int(context.args[0])
        plan_index = int(context.args[1]) - 1

        plan = plan_list[plan_index]

        if idx < 0 or idx >= len(configs.get(plan, [])):
            await update.message.reply_text('❌ ایندکس اشتباه')
            return

        removed = configs[plan].pop(idx)
        save_configs()

        await update.message.reply_text(f'🗑 حذف شد:\n{removed}')

    except Exception:
        msg = "❌ فرمت: /remove <index> <plan 1-5>\n\n"
        for i, p in enumerate(plan_list, 1):
            msg += f"{i} = {p}\n"
        await update.message.reply_text(msg)


# ----------------- TEXT HANDLER -----------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id
    admin_id = context.bot_data['admin_id']

    if text == '📞 پشتیبانی':
        await update.message.reply_text(SUPPORT_ID)
        return

    if text == '📦 پلن‌ها':
        msg = '📦 پلن‌ها:\n\n'
        for p, price in plans.items():
            msg += f"{p}: {price} تومان\n"
        await update.message.reply_text(msg)
        return

    if text == '🛒 خرید VPN':
        if not state['shop_open']:
            await update.message.reply_text('🔴 فروشگاه بسته است.')
            return

        kb = [[p] for p in plans]
        kb.append(['🏠 برگشت'])

        await update.message.reply_text(
            'پلن انتخاب کن:',
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return

    if text == '🏠 برگشت':
        await update.message.reply_text('🏠', reply_markup=main_keyboard())
        return

    if text in plans:
        if not state['shop_open']:
            await update.message.reply_text('🔴 فروشگاه بسته است.')
            return

        if len(configs.get(text, [])) == 0:
            await update.message.reply_text('❌ این پلن موجود نیست.')
            return

        config = configs[text].pop(0)
        save_configs()

        pending_orders[uid] = {
            'plan': text,
            'config': config
        }

        await update.message.reply_text(
            f"""📌 پلن: {text}
💰 {plans[text]} تومان

💳 {CARD_NUMBER}
👤 {CARD_OWNER}

📸 بعد از پرداخت رسید بفرست."""
        )
        return

    await update.message.reply_text('از منو استفاده کن 👇', reply_markup=main_keyboard())


# ----------------- PHOTO (RECEIPT) -----------------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    admin_id = context.bot_data['admin_id']

    if uid not in pending_orders:
        await update.message.reply_text('❌ ابتدا یک پلن انتخاب کن.')
        return

    order = pending_orders[uid]
    username = update.effective_user.username or str(uid)

    caption = (
        f"📬 رسید از @{username}\n"
        f"📌 پلن: {order['plan']}\n"
        f"💰 {plans[order['plan']]} تومان"
    )

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton('✅ تایید', callback_data=f'approve|{uid}'),
        InlineKeyboardButton('❌ رد', callback_data=f'reject|{uid}')
    ]])

    await context.bot.send_photo(
        admin_id,
        photo=update.message.photo[-1].file_id,
        caption=caption,
        reply_markup=kb
    )

    await update.message.reply_text('✅ رسید دریافت شد.')


# ----------------- CALLBACK -----------------
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data
    admin_id = context.bot_data['admin_id']

    if q.from_user.id != admin_id:
        return

    if data.startswith('approve|'):
        target = int(data.split('|')[1])

        if target not in pending_orders:
            await q.message.edit_caption('❌ سفارش پیدا نشد.')
            return

        order = pending_orders.pop(target)

        try:
            await context.bot.send_message(
                target,
                f"🎉 تایید شد!\n📌 {order['plan']}\n\n<code>{order['config']}</code>",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(e)
            configs.setdefault(order['plan'], []).insert(0, order['config'])
            save_configs()

        await q.message.edit_caption('✅ ارسال شد.')
        return

    if data.startswith('reject|'):
        target = int(data.split('|')[1])

        if target in pending_orders:
            order = pending_orders.pop(target)
            configs.setdefault(order['plan'], []).insert(0, order['config'])
            save_configs()

        await context.bot.send_message(target, '❌ رسید رد شد.')
        await q.message.edit_caption('🚫 رد شد.')


# ----------------- MAIN -----------------
def main():
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    admin_id = os.environ.get('ADMIN_ID')

    if not token or not admin_id:
        logger.error("Missing ENV variables")
        return

    load_configs()

    app = ApplicationBuilder().token(token).build()

    app.bot_data['admin_id'] = int(admin_id)

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('stock', cmd_stock))
    app.add_handler(CommandHandler('open', cmd_open))
    app.add_handler(CommandHandler('close', cmd_close))

    app.add_handler(CommandHandler('add1', add_config))
    app.add_handler(CommandHandler('add2', add_config))
    app.add_handler(CommandHandler('add3', add_config))
    app.add_handler(CommandHandler('add4', add_config))
    app.add_handler(CommandHandler('add5', add_config))

    app.add_handler(CommandHandler('remove', cmd_remove))

    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("Bot started")
    app.run_polling(drop_pending_updates=True)


# ----------------- RUN -----------------
if __name__ == '__main__':
    main()
