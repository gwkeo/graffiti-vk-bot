import io
import json
import os
import uuid
from urllib.parse import urlencode

import requests
import telebot
import markups
from PIL import Image, ImageDraw

token = os.environ['TOKEN']
mini_app_url = os.environ['MINI_APP_URL']
bot_tag = os.environ.get('BOT_TAG', '@your_bot_tag')

bot = telebot.TeleBot(token)
draw_sessions = {}


def make_draw_url(user_id: int, chat_id: int, message_id: int, session_id: str) -> str:
    params = urlencode({
        'user_id': user_id,
        'chat_id': chat_id,
        'message_id': message_id,
        'session_id': session_id,
    })
    separator = '&' if '?' in mini_app_url else '?'
    return f'{mini_app_url}{separator}{params}'


def render_drawing(payload: dict) -> io.BytesIO:
    width = int(payload.get('w', 512))
    height = int(payload.get('h', 512))
    width = max(128, min(width, 1024))
    height = max(128, min(height, 1024))

    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    for stroke in payload.get('s', []):
        points = []
        for pair in str(stroke.get('p', '')).split():
            try:
                x_raw, y_raw = pair.split(',', 1)
                x = round(int(x_raw) * width / 1000)
                y = round(int(y_raw) * height / 1000)
            except (TypeError, ValueError):
                continue
            points.append((x, y))

        if not points:
            continue

        color = '#ffffff' if stroke.get('e') else stroke.get('c', '#000000')
        line_width = max(1, min(int(stroke.get('z', 3)), 64))

        if len(points) == 1:
            x, y = points[0]
            radius = max(1, line_width // 2)
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
        else:
            draw.line(points, fill=color, width=line_width, joint='curve')

    output = io.BytesIO()
    image.save(output, format='PNG')
    output.name = 'drawing.png'
    output.seek(0)
    return output


def edit_message_with_photo(chat_id: int, message_id: int, image: io.BytesIO, caption: str):
    response = requests.post(
        f'https://api.telegram.org/bot{token}/editMessageMedia',
        data={
            'chat_id': chat_id,
            'message_id': message_id,
            'media': json.dumps({
                'type': 'photo',
                'media': 'attach://drawing',
                'caption': caption,
            }),
        },
        files={'drawing': ('drawing.png', image, 'image/png')},
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()
    if not result.get('ok'):
        raise RuntimeError(result.get('description', 'Telegram rejected editMessageMedia'))


def safe_int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@bot.message_handler(commands=["start"])
def start_message(message):
    bot.send_message(chat_id=message.chat.id, text=message.text)

@bot.message_handler(commands=["draw"])
def draw_message(message):
    sent = bot.send_message(chat_id=message.chat.id, text="click the button below to draw")
    session_id = uuid.uuid4().hex
    draw_sessions[session_id] = {
        'user_id': message.from_user.id,
        'chat_id': sent.chat.id,
        'message_id': sent.message_id,
    }
    url = make_draw_url(message.from_user.id, sent.chat.id, sent.message_id, session_id)
    bot.edit_message_reply_markup(
        chat_id=sent.chat.id,
        message_id=sent.message_id,
        reply_markup=markups.initial_menu(url),
    )


@bot.message_handler(content_types=['web_app_data'])
def draw_result(message):
    try:
        payload = json.loads(message.web_app_data.data)
    except (TypeError, json.JSONDecodeError):
        bot.reply_to(message, 'Не получилось прочитать рисунок.')
        return

    session_id = payload.get('session_id')
    session = draw_sessions.get(session_id)
    if not session:
        bot.reply_to(message, 'Сессия рисования устарела. Запустите /draw еще раз.')
        return

    if session['user_id'] != message.from_user.id:
        bot.reply_to(message, 'Этот рисунок должен отправить пользователь, который запускал /draw.')
        return

    if (
        safe_int(payload.get('user_id')) != session['user_id']
        or safe_int(payload.get('chat_id')) != session['chat_id']
        or safe_int(payload.get('message_id')) != session['message_id']
    ):
        bot.reply_to(message, 'Данные сессии не совпали. Запустите /draw еще раз.')
        return

    image = render_drawing(payload)
    caption = f'сделано в {bot_tag}'
    edit_message_with_photo(session['chat_id'], session['message_id'], image, caption)
    draw_sessions.pop(session_id, None)
    bot.reply_to(message, 'Готово.')


bot.infinity_polling()
