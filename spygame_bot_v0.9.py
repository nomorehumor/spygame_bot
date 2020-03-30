# -*- coding: utf-8 -*-

import telebot
import threading

bot = telebot.TeleBot('1062169710:AAF-KZFJoLjy1nlS7GdR0F9Z9KWcbS2ha2A')

ingame_users = []
ready_users = []
chats_ids = []

game_started = False

timer = None

ready_keyboard = telebot.types.InlineKeyboardMarkup()
ready_button = telebot.types.InlineKeyboardButton(text='готов')
ready_button.callback_data = 'ready'
ready_keyboard.add(ready_button)

empty_ready_keyboard = telebot.types.InlineKeyboardMarkup()
ready_button.callback_data = 'wasted'
empty_ready_keyboard.add(ready_button)

not_ready_keyboard = telebot.types.InlineKeyboardMarkup()
not_ready_button = telebot.types.InlineKeyboardButton(text='не готов')
not_ready_button.callback_data = 'not_ready'
not_ready_keyboard.add(not_ready_button)

empty_not_ready_keyboard = telebot.types.InlineKeyboardMarkup()
not_ready_button.callback_data = 'wasted'
empty_not_ready_keyboard.add(not_ready_button)


@bot.message_handler(commands=['start'])
def start_message(message):
    print(message.text)
    bot.send_message(message.chat.id, 'Привет')
    if message.from_user.username not in ingame_users:
        start_session(message)


@bot.message_handler(commands=['again'])
def start_session(message):
    if message.from_user.username not in ingame_users:
        ingame_users.append(message.from_user.username)
        chats_ids.append(message.chat.id)

    send_users_list('игроки: ')

    bot.send_message(message.chat.id, 'Нажми готов, чтобы начать игру', reply_markup=ready_keyboard)


@bot.message_handler(content_types=['text'])
def on_send_text(message):
    print(message.text)


def broadcast(text, keyboard=None):
    for chat_id in chats_ids:
        bot.send_message(chat_id, text, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def get_ready(call):
    global game_started
    if call.data == 'wasted':
        bot.answer_callback_query(call.id, 'не нажимай на старые кнопки')
    if call.data == 'ready':
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=empty_ready_keyboard)
        if not game_started:
            bot.answer_callback_query(call.id, text='понял, принял')
            ready_users.append(call.from_user.username)
            send_users_list('игроки:')
            prepare_game()
        else:
            bot.answer_callback_query(call.id, 'не ломай меня пожалуйсто')

    elif call.data == 'not_ready':
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=empty_not_ready_keyboard)
        global timer
        timer.cancel()
        timer = threading.Timer(5.0, start_game)
        game_started = False
        bot.answer_callback_query(call.id, text='отменено')
        broadcast('игра отменена игроком @' + call.from_user.username)
        ready_users.remove(call.from_user.username)
        send_users_list('игроки:')
        broadcast('кто не готов, пусть нажмет ', ready_keyboard)


def send_users_list(text):
    """Takes chat id and starting text and sends users list"""
    send_string = text + '\n'
    for user in ingame_users:
        send_string += '@' + user
        if user in ready_users:
            send_string += ' ✅ \n'
        else:
            send_string += ' ❌ \n'
    broadcast(send_string)


def prepare_game():
    for user in ingame_users:
        if user not in ready_users:
            break
    else:
        broadcast("вроде все готовы, начинаю игру через 5 секунд, "
                  "нажмите 'не готов', чтобы остановить ", not_ready_keyboard)
        global timer
        timer = threading.Timer(5.0, start_game)
        timer.start()
        global game_started
        game_started = True


def start_game():
    broadcast('начинаю игру...')
    broadcast('.......................'
              '.......................')
    again_timer = threading.Timer(5.0, broadcast, args=['для начала новой игры нажмите /again'])
    again_timer.start()
    reset_timer = threading.Timer(6.0, reset_users)
    reset_timer.start()

    global game_started
    game_started=False


def reset_users():
    global ready_users
    ready_users = []
    global ingame_users
    ingame_users = []
    global chats_ids
    chats_ids = []


bot.polling()


