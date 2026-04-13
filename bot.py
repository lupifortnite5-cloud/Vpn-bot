import os
import json
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
ApplicationBuilder, CommandHandler, MessageHandler,
ContextTypes, filters,
)

logging.basicConfig(format=’%(asctime)s - %(levelname)s - %(message)s’, level=logging.INFO)
logger = logging.getLogger(**name**)

SUPPORT_ID = ‘@your_support_id’
CARD_NUMBER = ‘6221061258771031’
CARD_OWNER = ‘ایروانی’

plans = {
‘1 گیگ - یک ماهه’: 400,
‘2 گیگ - یک ماهه’: 800,
‘3 گیگ - یک ماهه’: 1200,
‘4 گیگ - یک ماهه’: 1600,
‘5 گیگ - یک ماهه’: 2000,
}
plan_list = list(plans.keys())

state = {‘shop_open’: True}
pending_orders = {}

def load_configs():
try:
with open(‘data.json’, ‘r’, encoding=‘utf-8’) as f:
d = json.load(f)
return d.get(‘configs’, {p: [] for p in plans})
except Exception:
return {p: [] for p in plans}

def save_configs():
with open(‘data.json’, ‘w’, encoding=‘utf-8’) as f:
json.dump({‘configs’: configs}, f, ensure_ascii=False, indent=2)

configs = load_configs()

def main_keyboard(uid, admin_id):
kb = [
[‘🛒 خرید VPN’],
[‘📦 پلن‌ها’],
[‘📞 پشتیبانی’],
]
return ReplyKeyboardMarkup(kb, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
uid = update.effective_user.id
admin_id = context.bot_data[‘admin_id’]
await update.message.reply_text(‘سلام 👋 به ربات VPN خوش اومدی!’, reply_markup=main_keyboard(uid, admin_id))

# — دستورادمین —

async def cmd_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.effective_user.id != context.bot_data[‘admin_id’]:
return
msg = ‘📦 موجودی استاک:\n\n’
for i, p in enumerate(plan_list, 1):
msg += f’{i}. {p}: {len(configs.get(p, []))} عدد\n’
await update.message.reply_text(msg)

async def cmd_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.effective_user.id != context.bot_data[‘admin_id’]:
return
state[‘shop_open’] = True
await update.message.reply_text(‘🟢 فروشگاه باز شد.’)

async def cmd_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.effective_user.id != context.bot_data[‘admin_id’]:
return
state[‘shop_open’] = False
await update.message.reply_text(‘🔴 فروشگاه بسته شد.’)

async def add_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.effective_user.id != context.bot_data[‘admin_id’]:
return
parts = update.message.text.split(None, 1)
cmd = parts[0].split(’@’)[0]
if len(parts) < 2 or not parts[1].strip():
await update.message.reply_text(‘❌ مثال: /add1 vless://…’)
return
mapping = {
‘/add1’: plan_list[0], ‘/add2’: plan_list[1], ‘/add3’: plan_list[2],
‘/add4’: plan_list[3], ‘/add5’: plan_list[4],
}
plan = mapping.get(cmd)
if not plan:
await update.message.reply_text(‘❌ دستور نامعتبر.’)
return
configs[plan].append(parts[1].strip())
save_configs()
await update.message.reply_text(f’✅ اضافه شد\n📌 {plan}\n📦 موجودی: {len(configs[plan])}’)

async def cmd_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.effective_user.id != context.bot_data[‘admin_id’]:
return
if not context.args or len(context.args) < 2:
msg = ‘❌ فرمت: /remove <index> <plan_number>\n\n’
for i, p in enumerate(plan_list, 1):
msg += f’{i} = {p}\n’
await update.message.reply_text(msg)
return
try:
idx = int(context.args[0])
plan_num = int(context.args[1]) - 1
p = plan_list[plan_num]
if idx < 0 or idx >= len(configs[p]):
await update.message.reply_text(f’❌ ایندکس اشتباه. موجودی {p}: {len(configs[p])}’)
return
removed = configs[p].pop(idx)
save_configs()
await update.message.reply_text(f’🗑 حذف شد:\n{removed}’)
except (ValueError, IndexError):
await update.message.reply_text(‘❌ فرمت: /remove <index> <plan_number 1-5>’)

# — تکست —

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
text = update.message.text
uid = update.effective_user.id
admin_id = context.bot_data[‘admin_id’]

```
if text == '📞 پشتیبانی':
    await update.message.reply_text(f'📞 {SUPPORT_ID}')
    return

if text == '📦 پلن‌ها':
    msg = '📦 پلن‌ها:\n\n'
    for p, price in plans.items():
        msg += f'  {p}: {price} تومان\n'
    await update.message.reply_text(msg)
    return

if text == '🛒 خرید VPN':
    if not state['shop_open']:
        await update.message.reply_text('🔴 فروشگاه بسته است.')
        return
    kb = [[p] for p in plans]
    kb.append(['🏠 برگشت'])
    await update.message.reply_text('پلن مورد نظرت رو انتخاب کن:', reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return

if text == '🏠 برگشت':
    await update.message.reply_text('🏠', reply_markup=main_keyboard(uid, admin_id))
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
    pending_orders[uid] = {'plan': text, 'config': config}
    await update.message.reply_text(
        f'پلن: {text}\n💰 {plans[text]} تومان\n\n💳 {CARD_NUMBER}\n👤 {CARD_OWNER}\n\n📸 بعد از پرداخت رسید بفرست.'
    )
    return

await update.message.reply_text('از منو استفاده کن 👇', reply_markup=main_keyboard(uid, admin_id))
```

# — عکس (رسید) —

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
uid = update.effective_user.id
admin_id = context.bot_data[‘admin_id’]
if uid not in pending_orders:
await update.message.reply_text(‘❌ ابتدا یک پلن انتخاب کن.’)
return
order = pending_orders[uid]
username = update.effective_user.username or str(uid)
caption = f’📬 رسید از @{username}\n📌 پلن: {order[“plan”]}\n💰 {plans[order[“plan”]]} تومان’
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
kb = InlineKeyboardMarkup([[
InlineKeyboardButton(‘✅ تایید’, callback_data=f’approve|{uid}’),
InlineKeyboardButton(‘❌ رد’, callback_data=f’reject|{uid}’),
]])
await context.bot.send_photo(admin_id, photo=update.message.photo[-1].file_id, caption=caption, reply_markup=kb)
await update.message.reply_text(‘✅ رسید دریافت شد. منتظر تایید ادمین باش.’)

# — callback تایید/رد —

async def handle_callback(update, context):
from telegram.ext import ContextTypes
q = update.callback_query
await q.answer()
uid = q.from_user.id
admin_id = context.bot_data[‘admin_id’]
data = q.data

```
if data.startswith('approve|'):
    if uid != admin_id:
        return
    target = int(data.split('|')[1])
    if target not in pending_orders:
        await q.message.edit_caption('❌ سفارش پیدا نشد.')
        return
    order = pending_orders.pop(target)
    cfg = order['config']
    plan = order['plan']
    try:
        await context.bot.send_message(target, f'🎉 تایید شد!\n📌 {plan}\n\n<code>{cfg}</code>', parse_mode='HTML')
    except Exception as e:
        logger.error(f'send config error: {e}')
        configs[plan].insert(0, cfg)
        save_configs()
        await q.message.edit_caption(f'❌ خطا در ارسال: {e}')
        return
    await q.message.edit_caption(f'✅ کانفیگ برای {target} ارسال شد.')
    return

if data.startswith('reject|'):
    if uid != admin_id:
        return
    target = int(data.split('|')[1])
    if target in pending_orders:
        order = pending_orders.pop(target)
        configs[order['plan']].insert(0, order['config'])
        save_configs()
    try:
        await context.bot.send_message(target, '❌ رسید رد شد. با پشتیبانی تماس بگیر.')
    except Exception as e:
        logger.error(f'reject notify error: {e}')
    await q.message.edit_caption('🚫 رد شد.')
    return
```

def main():
token = os.environ.get(‘TELEGRAM_BOT_TOKEN’)
admin_id_str = os.environ.get(‘ADMIN_ID’)
if not token:
logger.error(‘TELEGRAM_BOT_TOKEN not set!’)
return
if not admin_id_str:
logger.error(‘ADMIN_ID not set!’)
return
admin_id = int(admin_id_str)
logger.info(f’Bot starting - Admin: {admin_id}’)
from telegram.ext import CallbackQueryHandler
app = ApplicationBuilder().token(token).build()
app.bot_data[‘admin_id’] = admin_id
app.add_handler(CommandHandler(‘start’, start))
app.add_handler(CommandHandler(‘stock’, cmd_stock))
app.add_handler(CommandHandler(‘open’, cmd_open))
app.add_handler(CommandHandler(‘close’, cmd_close))
app.add_handler(CommandHandler(‘add1’, add_config))
app.add_handler(CommandHandler(‘add2’, add_config))
app.add_handler(CommandHandler(‘add3’, add_config))
app.add_handler(CommandHandler(‘add4’, add_config))
app.add_handler(CommandHandler(‘add5’, add_config))
app.add_handler(CommandHandler(‘remove’, cmd_remove))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(handle_callback))
logger.info(‘Bot is running!’)
app.run_polling(drop_pending_updates=True)

if **name** == ‘**main**’:
main()
