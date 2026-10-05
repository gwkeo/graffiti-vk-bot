import telebot
import os

token = os.environ['TOKEN']

bot = telebot.TeleBot(token)
@bot.message_handler(commands=["start"])
def start_message(message):
    bot.send_message(chat_id=message.chat.id, text=message.text)

bot.infinity_polling()

