# -*- coding: utf-8 -*-
import telebot
import threading
import os
import datetime
import random

token = os.environ['TEST_BOT_TOKEN']
if token is None:
    print("No bot token found in environments variables")
    quit()

bot = telebot.TeleBot(token)

class User:
    def __init__(self, username, chat_id):
        self.username = username
        self.chat_id = chat_id

    def __str__(self):
        return f"User: ({self.username}, {self.chat_id})"

ingame_users = []
ready_users = []

game_started = False

word = None

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
    bot.send_message(message.chat.id, 'Hi')
    for user in ingame_users:
        if message.from_user.username == user.username:
            break
    if get_user_by_username(message.from_user.username) is None:
        start_session(message)


@bot.message_handler(commands=['again'])
def start_session(message):
    if get_user_by_username(message.from_user.username) is None:
        ingame_users.append(User(message.from_user.username, message.chat.id))

    send_game_info()
    bot.send_message(message.chat.id, 'Type /ready, to start the game')


def broadcast(text, keyboard=None):
    for user in ingame_users:
        bot.send_message(user.chat_id, text, reply_markup=keyboard)

def get_user_by_username(username):
    global ingame_users
    for user in ingame_users:
        if user.username == username:
            return user
    else: 
        return None

@bot.message_handler(commands=['ready'])
def get_ready(message):
    global game_started
    print(game_started)
    if game_started is False:
        print("Preparing the game")
        user = get_user_by_username(message.from_user.username)
        ready_users.append(user)
        send_game_info()
        prepare_game()
        broadcast("Type /not_ready, if somebody is not ready ")
    else:
        bot.send_message(message.chat.id, 'game is already running')


@bot.message_handler(commands=['not_ready'])
def cancel_game(message):
    global timer
    global game_started
    if game_started is True:
        timer.cancel()
        timer = threading.Timer(5.0, start_game)
        game_started=False
        broadcast('game was cancelled by: @' + message.from_user.username)
        ready_users.remove(message.from_user.username)
        send_game_info()
        broadcast('the one, who is ready again, must type /ready')


@bot.message_handler(commands=['set_word'])
def set_word(message):
    global word
    word = " ".join(message.text.split(" ")[1:])
    if word != "":
        print(f"set the word: {word}")
        broadcast("The word was set")
        prepare_game()

@bot.message_handler(commands=['unset_word'])
def unset_word(message):
    global word
    word = None
    broadcast("The word was unset")

@bot.message_handler(commands=['debug'])
def debug_info(message):
    bot.send_message(message.chat.id,
                     "ingame_users: " + str(ingame_users) + "\n" +
                     "ready_users: " + str(ready_users) + "\n" )

@bot.message_handler(content_types=['text'])
def on_send_text(message):
    print(datetime.datetime.now(), "|",
    message.from_user.username + ": " +  message.text)

def send_game_info():
    """Takes chat id and something to say in the beginning of line text and sends users list"""
    send_string = "Players:" + '\n'
    for user in ingame_users:
        send_string += '@' + user.username
        if user in ready_users:
            send_string += ' ✅ \n'
        else:
            send_string += ' ❌ \n'
    send_string += '\n'
    if word is None:
        send_string += "The word wasn't set yet. Type /set_word 'word' to set it"
    else:
        send_string += "The word is already set. Type /unset_word to unset"

    broadcast(send_string)


def prepare_game():
    min_players = 1
    for user in ingame_users:
        if user not in ready_users:
            break
    else:
        if len(ready_users) >= min_players:
            if word is not None: 
                global timer
                global game_started
                broadcast("seems like everyone is ready, starting the game after 5 seconds, "
                        "type /not_ready, to stop")
                timer = threading.Timer(5.0, start_game)
                timer.start()
                game_started = True
            else:
                broadcast("We can start, everything that left is the word ")
        else:
            broadcast("{} more people needed for game".format(min_players - len(ready_users)))


def start_game():
    global game_started
    broadcast('starting the game...')
    broadcast('....................... \n'
              '.......................')
    again_timer = threading.Timer(5.0, broadcast, args=['for new game type /again'])
    again_timer.start()
    reset_timer = threading.Timer(6.0, reset_users)
    reset_timer.start()

    #choose spies
    spies_number = 0
    if len(ready_users) <= 4:
        spies_number = 1
    else:
        spies_number = random.randint(len(ready_users) // 4, len(ready_users) // 4 + 1)
    print(f"number of spies: {spies_number}")
    spies = random.sample(ready_users, spies_number)

    tell_word(spies, word)

    game_started=False
    word = None
    

def tell_word(spies_list, word):
    for user in ready_users:
        if user in spies_list:
            bot.send_message(user.chat_id, "you're the spy")
        else:
            bot.send_message(user.chat_id, word)


def reset_users():
    global ready_users
    global ingame_users
    ready_users = []
    ingame_users = []


bot.polling()


