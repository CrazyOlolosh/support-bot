import os
import logging
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler
import requests

BOT_TOKEN = os.environ.get('BOT_TOKEN')
USEDESK_TOKEN = os.environ.get('USEDESK_TOKEN')
PORT = int(os.environ.get('PORT', '8443'))
HEROKU_APP_NAME = os.getenv("HEROKU_APP_NAME")

status_list = {
    1: 'Открыт',
    2: 'Выполнен',
    3: 'Закрыт',
    4: 'Удален',
    5: 'На удержании',
    6: 'В ожидании',
    7: 'Спам',
    8: 'Новый',
    9: 'Рассылка',
    10: 'Объединен',
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Привет, чем могу помочь?")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    req = requests.get(f'https://api.usedesk.ru/ticket?api_token={USEDESK_TOKEN}&ticket_id={context.args}')
    resp = req.json()
    print(resp)
    try:
        t_status = resp['ticket']['ststus_id']
        result = status_list[t_status]
        status_result = f'Текущий статус обращения №{context.args}: {result}.'
    except KeyError:
        status_result = "Вы ввели неверный номер обращения. Пожалуйста, попробуйте ещё."
    await context.bot.send_message(chat_id=update.effective_chat.id, text=status_result)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler('start', start)
    status_handler = CommandHandler('status', status)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)

    application.add_handler(start_handler)
    application.add_handler(status_handler)
    application.add_handler(echo_handler)

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"https://{HEROKU_APP_NAME}.herokuapp.com/{BOT_TOKEN}"
    )

    application.bot.set_webhook(f"https://{HEROKU_APP_NAME}.herokuapp.com/{BOT_TOKEN}")
    application.idle()
