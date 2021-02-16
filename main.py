#!/usr/bin/env python

from json import load, dump
from logging import basicConfig, INFO, getLogger

from requests import get
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=INFO)
logger = getLogger(__name__)
CHECK_ADD, ADD, DELETE = range(3)
personal_data = load(open("personal_data.json"))


def get_user(user_id, api_key):
    url = "https://osu.ppy.sh/api/get_user?k={}&u={}"
    ready_url = url.format(api_key, user_id)
    return get(ready_url).json()


def write_data_json(name_json, data_json):
    with open(name_json, "w") as j:
        dump(obj=data_json, fp=j, indent=2)


def start(update: Update, context: CallbackContext):

    first_name = update.message.from_user.first_name
    chat_id = update.effective_chat.id
    logger.info("Чел стартанул: %s / chat: %s", first_name, chat_id)
    update.message.reply_text(
        'Привет! Я бот на стадии теста. '
        'Моя задача уведомлять тебя, когда кто-нибудь будет играть твои карты в мультиплеере. '
        'Чтобы прекратить со мной разговор отправь /cancel.',
        reply_markup=ReplyKeyboardRemove()
    )
    if str(update.effective_chat.id) in load(open("db.json")):
        logger.info("Чел уже есть в базе: %s / chat: %s", first_name, chat_id)
        reply_keyboard = [['Прекратить']]
        update.message.reply_text(
            'Ты уже есть в базе. Хочешь прекратить отслеживание? ',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return DELETE
    logger.info("Чела нет в базе: %s / chat: %s", first_name, chat_id)
    update.message.reply_text('Начинаем? Введи имя своего профиля osu или ID', reply_markup=ReplyKeyboardRemove())
    return CHECK_ADD


def check_add(update: Update, context: CallbackContext):
    first_name = update.message.from_user.first_name
    chat_id = update.effective_chat.id
    osu_profil = update.message.text
    if get_user(osu_profil.encode('ascii', errors='ignore').decode(), personal_data["api_key"]):
        context.user_data['osu_profile'] = osu_profil
        reply_keyboard = [['Да, все верно'], ['Нет, я ошибся']]
        s = "https://osu.ppy.sh/users/" + osu_profil
        update.message.reply_text(
            s + '\nЭто ваш профиль?',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return ADD
    logger.info("Чела ошибся: %s / chat: %s / osu profile: %s", first_name, chat_id, osu_profil)
    update.message.reply_text(
        'Такого профиля несуществует. '
        'Нажмите /start, чтобы начать с начала',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def add(update: Update, context: CallbackContext):
    first_name = update.message.from_user.first_name
    chat_id = str(update.effective_chat.id)
    osu_profile = context.user_data['osu_profile']
    if update.message.text == 'Нет, я ошибся':
        logger.info("Чел ошибся: %s / chat: %s / osu profile: %s", first_name, chat_id, osu_profile)
        update.message.reply_text('Нажмите /start, чтобы начать с начала', reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    logger.info("Добавился чел: %s / chat: %s / osu profile: %s", first_name, chat_id, osu_profile)
    db = load(open("db.json"))
    db[chat_id] = osu_profile
    write_data_json("db.json", db)
    update.message.reply_text('Вы были добавлены. Добро пожаловать!', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def delete(update: Update, context: CallbackContext):
    first_name = update.message.from_user.first_name
    chat_id = str(update.effective_chat.id)
    db = load(open("db.json"))
    logger.info("Удалился чел: %s / chat: %s / osu profile: %s", first_name, chat_id, db[chat_id])
    del db[chat_id]
    write_data_json("db.json", db)
    update.message.reply_text('Слежение было прекращено. Жаль с вами расставаться', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext):
    first_name = update.message.from_user.first_name
    chat_id = str(update.effective_chat.id)
    logger.info("Челу %s что-то непонравилось / chat: %s", first_name, chat_id)
    update.message.reply_text('До встречи', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    updater = Updater(personal_data["token_telegram_bot"])
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHECK_ADD: [MessageHandler(Filters.text & ~Filters.command, check_add)],
            ADD: [MessageHandler(Filters.text & ~Filters.command, add)],
            DELETE: [MessageHandler(Filters.text & ~Filters.command, delete)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    # every(2).seconds.do(osu)
    # while True:
    #     run_pending()
    #     sleep(1)


if __name__ == '__main__':
    main()
