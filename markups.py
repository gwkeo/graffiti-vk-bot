from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def initial_menu(id: int):
    draw_button = InlineKeyboardButton("Draw", callback_data=f"draw_button:{id}")
    initial_keyboard = InlineKeyboardMarkup()
    initial_keyboard.add(draw_button)
    return initial_keyboard
