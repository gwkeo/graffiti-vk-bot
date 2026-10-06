import telebot
import os
import markups

token = os.environ['TOKEN']

bot = telebot.TeleBot(token)
@bot.message_handler(commands=["start"])
def start_message(message):
    bot.send_message(chat_id=message.chat.id, text=message.text)

@bot.message_handler(commands=["draw"])
def draw_message(message):
    bot.send_message(chat_id=message.chat.id, text="click the button below to draw", reply_markup=markups.initial_menu(0))
bot.infinity_polling()

