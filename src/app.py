import os

from dotenv import load_dotenv
from telebot import TeleBot, types


import config
from logic import start_program, check_tg_usr, check_button_call
from database import get_role_user
from buttons import start_buttons

bot = TeleBot(config.token)
start_program()


@bot.message_handler(commands=['start'])
def start_message(message: types.Message):
    if message.from_user.is_bot:
        bot.send_message(message.chat.id, "Доступ запрещен")
        return
    if not check_tg_usr(bot, message):
        return

    bot.send_message(message.chat.id,
                     'Доступные команды',
                     reply_markup=start_buttons.get_markup(role=get_role_user(message.chat.id)))


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.from_user.is_bot:
        bot.send_message(message.chat.id, "Доступ запрещен")
        return
    if not check_tg_usr(bot, call.message):
        return
    check_button_call(bot,call, get_role_user(call.from_user.id))
    bot.answer_callback_query(call.id)

bot.infinity_polling()
