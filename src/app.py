import telebot
from logic import get_all_username

token = "7350977496:AAF0krjG8DmLI9O0LgkzvhpEn4INlVYW9R0"

bot=telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id,"Привет, проверяем разрешен ли вам доступ к системе")
    
    
@bot.message_handler(commands=['all'])
def start_message(message):
    bot.send_message(message.chat.id, f"Все пользователи {get_all_username()}")


bot.infinity_polling()