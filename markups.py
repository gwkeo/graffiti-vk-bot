from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo


def initial_menu(url: str):
    draw_button = InlineKeyboardButton("Draw", web_app=WebAppInfo(url=url))
    initial_keyboard = InlineKeyboardMarkup()
    initial_keyboard.add(draw_button)
    return initial_keyboard
