from telebot import TeleBot, types
from logic import start_program, check_button, get_markup, check_tg_usr
from database import get_role_user
import os
from dotenv import load_dotenv
load_dotenv()

bot = TeleBot(os.getenv('token'))
start_program()


@bot.message_handler(commands=['start'])
def start_message(message: types.Message):
    if not check_tg_usr(bot, message):
        return
    bot.send_message(message.chat.id, 'Доступные команды', reply_markup=get_markup(get_role_user(message.chat.id)))


@bot.message_handler(content_types='text')
def message_reply(message: types.Message):
    if not check_tg_usr(bot, message):
        return
    check_button(bot, message, get_role_user(message.chat.id))


bot.infinity_polling()