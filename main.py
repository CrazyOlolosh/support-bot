import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from telegram.ext import (
    filters,
    MessageHandler,
    Application,
    ContextTypes,
    CommandHandler,
    ConversationHandler,
)
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN")
USEDESK_TOKEN = os.environ.get("USEDESK_TOKEN")
PORT = int(os.environ.get("PORT", "8443"))
HEROKU_APP_NAME = os.getenv("HEROKU_APP_NAME")

status_list = {
    1: "Открыт",
    2: "Выполнен",
    3: "Закрыт",
    4: "Удален",
    5: "На удержании",
    6: "В ожидании",
    7: "Спам",
    8: "Новый",
    9: "Рассылка",
    10: "Объединен",
}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

(INITIAL, NAME, MAIL, THEME, PRE_STATUS, STATUS, OTHER, NEW_TICKET, HELPFULL) = range(9)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    continue_keyboard = [[KeyboardButton("Продожить")]]
    await update.message.reply_text(
        "Привет​​! Напишите все вопросы, а мы ответим на каждый из них ❤️️\n"
        "Это может занять от пары минут до нескольких часов, но если мы не застанем вас тут, ответ найдет вас в почте.",
        reply_markup=InlineKeyboardMarkup(
            continue_keyboard,
            one_time_keyboard=True
        ),
    )

    return INITIAL


async def initial(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(f"Представьтесь пожалуйста", reply_markup=ReplyKeyboardRemove(),)

    return NAME


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    input_name = update.message.text
    context.user_data["name"] = input_name
    await update.message.reply_text(f"Здравствуйте, {input_name}! Укажите свой e-mail.", reply_markup=ReplyKeyboardRemove())

    return MAIL


async def mail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    theme_keyboard = [
        ["Хочу у Вас работать", "Хочу предложить сотрудничество"],
        ["Хочу узнать статус своего обращения", "У меня другой вопрос"],
    ]
    input_mail = update.message.text
    context.user_data["mail"] = input_mail
    await update.message.reply_text(
        f"Почта {input_mail} будет использоваться для обратной связи с Вами.\n"
        "Выберите тему обращения.",
        reply_markup=ReplyKeyboardMarkup(
            theme_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Выберите тему",
        ),
    )

    return THEME


async def job(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    help_keyboard = [["Да", "Нет"]]
    client_name = context.user_data["name"]
    await update.message.reply_text(
        f'Дорогой, {client_name}! Наши вакансии регулярно обновляются и публикуются на официальном сайте https://blackcaviar.games/ в разделе "Вакансии". Вы, также, можете направить Ваше резюме нам на почту job@blackcaviar.games.\n'
        "Благодарю за интерес, проявленный к нашей компании.😉\n\n Мой ответ помог Вам?",
        reply_markup=ReplyKeyboardMarkup(
            help_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Ответ помог?",
        ),
    )

    return HELPFULL


async def cooperate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    help_keyboard = [["Да", "Нет"]]
    client_name = context.user_data["name"]
    await update.message.reply_text(
        f"Дорогой, {client_name}! По вопросам сотрудничества Вы можете написать нам на почту info@blackcaviar.games.\n"
        "Благодарю за интерес, проявленный к нашей компании.😉\n\n Мой ответ помог Вам?",
        reply_markup=ReplyKeyboardMarkup(
            help_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Ответ помог?",
        ),
    )

    return HELPFULL


async def pre_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        f"""Введите пожалуйста номер Вашего обращения (он указан в письме)""", reply_markup=ReplyKeyboardRemove()
    )

    return STATUS


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_ticket = update.message.text
    req = requests.get(
        f"https://api.usedesk.ru/ticket?api_token={USEDESK_TOKEN}&ticket_id={input_ticket}"
    )
    resp = req.json()
    print(resp)
    try:
        t_status = resp["ticket"]["status_id"]
        result = status_list[t_status]
        status_result = f"Текущий статус обращения №{input_ticket}: {result}."
        await context.bot.send_message(chat_id=update.effective_chat.id, text=status_result)

        return HELPFULL
    except KeyError:
        status_result = "Вы ввели неверный номер обращения. Пожалуйста, попробуйте ещё."
        await context.bot.send_message(chat_id=update.effective_chat.id, text=status_result)


async def other(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(f"""Опишите пожалуйста суть Вашего обращения""", reply_markup=ReplyKeyboardRemove())

    return NEW_TICKET


async def new_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    input_ticket_text = update.message.text
    subject = "Новое обращение в боте Telegram"
    client = context.user_data["name"]
    mail = context.user_data["mail"]
    req = requests.post(f'https://api.usedesk.ru/create/ticket?api_token={USEDESK_TOKEN}&subject={subject}&message={input_ticket_text}&client_name={client}&client_email={mail}&tag=telegram&from=client')
    resp = req.json()
    print(resp)
    if resp['ticket_id']:
        await update.message.reply_text(f"""Большое спасибо за обращение!\nОно зарегистрировано под номером {resp['ticket_id']}.\nМы получили Ваш запрос и ответим Вам в скором времени. """,)

    return ConversationHandler.END


async def bye(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Был рад Вам помочь!\n"
        "Если у Вас возникнут еще какие-либо вопросы, пожалуйста свяжитесь с нами в любое удобное для Вас время. Спасибо за обращение.\n"
        "До свидания.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Пока пока. Буду рад снова поболтать", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


if __name__ == "__main__":
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            INITIAL: [MessageHandler(filters.TEXT, initial)],
            NAME: [MessageHandler(filters.TEXT, name)],
            MAIL: [MessageHandler(filters.TEXT, mail)],
            THEME: [
                MessageHandler(filters.Regex("(работать)"), job),
                MessageHandler(filters.Regex("(сотрудничество)"), cooperate),
                MessageHandler(filters.Regex("(статус)"), pre_status),
                MessageHandler(filters.Regex("(другой)"), other),
            ],
            PRE_STATUS: [MessageHandler(filters.Regex("(\d{8,9})"), pre_status)],
            STATUS: [MessageHandler(filters.TEXT, status)],
            OTHER: [MessageHandler(filters.TEXT, other)],
            NEW_TICKET: [MessageHandler(filters.TEXT, new_ticket)],
            HELPFULL: [
                MessageHandler(filters.Regex("(Да)"), bye),
                MessageHandler(filters.Regex("(Нет)"), other),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"https://{HEROKU_APP_NAME}.herokuapp.com/{BOT_TOKEN}",
    )

    application.bot.set_webhook(f"https://{HEROKU_APP_NAME}.herokuapp.com/{BOT_TOKEN}")
