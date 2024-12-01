import os
from datetime import datetime

import pytz
import requests
from telebot import telebot, types

# pip install pyTelegramBotAPI
# pip install pytz
# pip install requests

# Get token from token.txt file
token_file = open('token.txt', 'r')
token = token_file.read().strip() # Remove
token_file.close()

bot = telebot.TeleBot(token) # Set bot token

item_data = {} # Data for POST

# Get key from key.txt file
key_file = open('key.txt', 'r')
key = key_file.read().strip()
key_file.close()

markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
add_item = types.KeyboardButton("Добавить запись")
check_items = types.KeyboardButton("Посмотреть мои записи")
edit_items = types.KeyboardButton("Редактировать запись")
markup.add(add_item, check_items, edit_items)

cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
cancel = types.KeyboardButton("Отмена")
cancel_markup.add(cancel)

edit_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
edit_title = types.KeyboardButton("Название")
edit_description = types.KeyboardButton("Описание")
edit_tags = types.KeyboardButton("Теги")
edit_markup.add(edit_title, edit_description, edit_tags, cancel)

print("-"*7 + "BOT STARTED" + "-"*7)

# Start message
@bot.message_handler(commands=['start'])
def start_message(message):
    first_name = message.from_user.first_name  # Get user first name
    last_name = message.from_user.last_name  # Get user last name
    user_id = message.chat.id # Get user id

    bot.send_message(
        message.chat.id,
        f"Добро пожаловать, {first_name} {last_name or ''}! Что вы бы хотели сделать?",
        reply_markup=markup
    )

    log_message_generate(f"BOT sent to {first_name} {last_name or ''}({user_id}): Добро пожаловать, {first_name} {last_name or ''}! Что вы бы хотели сделать?")

@bot.message_handler(content_types=['text'])
def handle_messages(message):
    user_message = message.text  # Get the message text
    user_id = message.chat.id  # Get the user ID

    first_name = message.from_user.first_name  # Get user first name
    last_name = message.from_user.last_name  # Get user last name

    log_message_generate(f"{first_name} {last_name or ''}({user_id}) sent: {user_message} \n")

    if user_message == "Добавить запись":
        bot.send_message(user_id, "Введите название записи...", reply_markup=cancel_markup)
        log_message_generate(f"BOT sent to {first_name} {last_name or ''}({user_id}): Введите название записи...")
        bot.register_next_step_handler(message, set_title, item_data)

    elif user_message == "Посмотреть мои записи":
        items_markup = items_markup_generator(message)
        if items_markup == 0:
            return
        bot.send_message(user_id, "Какую именно запись вы бы хотели посмотреть?", reply_markup=items_markup)
        log_message_generate(f"BOT sent to {first_name} {last_name or ''}({user_id}): Какую именно запись вы бы хотели посмотреть?")
        bot.register_next_step_handler(message, check_items)

    elif user_message == "Редактировать запись":
        items_markup = items_markup_generator(message)
        if items_markup == 0:
            return
        bot.send_message(user_id, "Какую именно запись вы бы хотели изменить?", reply_markup=items_markup)
        log_message_generate(f"BOT sent to {first_name} {last_name or ''}({user_id}): Какую именно запись вы бы хотели изменить?")
        bot.register_next_step_handler(message, edit_item_chooser)

def set_title(message, data):
    user_id = message.chat.id

    log_message_generate(f"User {user_id} sent: {message.text} \n")

    if message.text == "Отмена":
        # Cancel item creation
        bot.send_message(
            user_id,
            "Действие отменено.",
            reply_markup=markup
        )
        log_message_generate(f"BOT to {user_id}: Добавление отменено.")
        return

    data["title"] = message.text # Add title

    bot.send_message(user_id, "Теперь опишите свою запись...")
    log_message_generate(f"BOT sent to {user_id}: Теперь опишите свою запись...")


    bot.register_next_step_handler(message, set_descr, data)

def set_descr(message, data):
    user_id = message.chat.id

    log_message_generate(f"User {user_id} sent: {message.text} \n")

    if message.text == "Отмена":
        # Cancel item creation
        bot.send_message(
            user_id,
            "Добавление отменено.",
            reply_markup=markup
        )
        log_message_generate(f"BOT sent to {user_id}: Добавление отменено.")
        return

    data["desc"] = message.text # Get description

    bot.send_message(user_id, "Теперь напишите теги через запятую... "
    "(Если вы напишите их по-другому, теги могут быть отправлены не корректно)")

    log_message_generate(f"BOT sent to {user_id}: Теперь напишите теги через запятую... "
    f"(Если вы напишите их по-другому, теги могут быть отправлены не корректно)")

    bot.register_next_step_handler(message, set_tags, data)

def set_tags(message, data):
    user_id = message.chat.id

    log_message_generate(f"User {user_id} sent: {message.text}")

    if message.text == "Отмена":
        # Cancel item creation
        bot.send_message(
            user_id,
            "Добавление отменено.",
            reply_markup=markup
        )
        log_message_generate(f"BOT sent to {user_id}: Добавление отменено.")
        return

    data["tags"] = message.text # Get tags

    post_item(message)

def check_items(message):
    user_id = message.chat.id
    user_answer = message.text

    log_message_generate(f"User {user_id} sent: {user_answer} \n")

    items = get_items(message)

    result = next((item for item in items if item['title'] == user_answer), None)

    if not result:
        bot.send_message(user_id, "Я не знаю такой записи!", reply_markup=markup)
        log_message_generate(f"BOT sent to {user_id}: Я не знаю такой записи!")
    else:
        bot.send_message(user_id, "Вот ваша запись:", reply_markup=markup)
        log_message_generate(f"BOT sent to {user_id}: Вот ваша запись:")

        bot.send_message(user_id, f"Название: {result['title']} \n \nОписание: {result['description']}")
        log_message_generate(f"BOT sent to {user_id}: Название: {result['title']} \n \nОписание: {result['description']}")

def edit_item_chooser(message):
    user_id = message.chat.id
    user_answer = message.text

    log_message_generate(f"User {user_id} sent: {user_answer} \n")

    items = get_items(message)

    result = next((item for item in items if item['title'] == user_answer), None)

    if not result:
        bot.send_message(user_id, "Я не знаю такой записи!", reply_markup=markup)
        log_message_generate(f"BOT sent to {user_id}: Я не знаю такой записи!")
        return
    elif user_answer == 'Отмена':
        bot.send_message(user_id, "Редактирование отменено", reply_markup=markup)
        log_message_generate(f"BOT sent to {user_id}: Редактирование отменено")
        return

    bot.send_message(user_id, "Что бы вы хотели бы изменить в этой записи?", reply_markup=edit_markup)
    log_message_generate(f"BOT sent to {user_id}: Что бы вы хотели бы изменить в этой записи?")

    bot.register_next_step_handler(message, edit_to_edit_chooser, result['id'])

def edit_to_edit_chooser(message, item_id,):
    user_answer = message.text
    user_id = message.chat.id

    log_message_generate(f"User {user_id} sent: {user_answer} \n")

    if user_answer == 'Название':
        bot.send_message(user_id, "Введите новое название...", reply_markup=cancel_markup)
        log_message_generate(f"BOT sent to {user_id}: Введите новое название...")

        bot.register_next_step_handler(message, edit_editor, item_id, 'title')
    elif user_answer == 'Описание':
        bot.send_message(user_id, "Введите новое описание...", reply_markup=cancel_markup)
        log_message_generate(f"BOT sent to {user_id}: Введите новое описание...")

        bot.register_next_step_handler(message, edit_editor, item_id, 'desc')
    elif user_answer == 'Теги':
        bot.send_message(user_id, "Введите новые теги...", reply_markup=cancel_markup)
        log_message_generate(f"BOT sent to {user_id}: Введите новые теги...")

        bot.register_next_step_handler(message, edit_editor, item_id, 'tags')
    elif user_answer == 'Отмена':
        bot.send_message(user_id, "Редактирование отменено", reply_markup=markup)
        log_message_generate(f"BOT sent to {user_id}: Редактирование отменено")
        return
    else:
        bot.send_message(user_id, "Нет такого варианта ответа!", reply_markup=markup)
        log_message_generate(f"BOT sent to {user_id}: Нет такого варианта ответа!")

def edit_editor(message, item_id, to_edit):
    user_id = message.chat.id
    user_answer = message.text

    log_message_generate(f"User {user_id} sent: {user_answer}")

    if user_answer == 'Отмена':
        bot.send_message(user_id, "Редактирование отменено", reply_markup=markup)
        log_message_generate(f"BOT sent to {user_id}: Редактирование отменено")
        return

    json = {'userId': user_id, 'itemId': item_id, f'{to_edit}': user_answer}
    header = {'key': key}
    url = "http://moktus.com/api/update-item"

    log_message_generate(f"USER {user_id} edit item {item_id}'s {to_edit} to {user_answer}")

    response = requests.post(url, headers=header, json=json)

    log_message_generate(f"SERVER json answer is: {response.json()}")
    log_message_generate(f"SERVER code answer is: {response.status_code}")

    if response.status_code == 200:
         bot.send_message(user_id, "Запись успешно отредактирована!")
         log_message_generate(f"BOT sent to {user_id}: Запись успешно отредактирована!")
    else:
         bot.send_message(user_id, f"Произошла ошибка во время отправки отредактированной записи, код ошибки: {response.status_code}")
         log_message_generate(f"BOT sent to {user_id}: Произошла ошибка во время отправки отредактированной записи, код ошибки: {response.status_code}")

def items_markup_generator(message):
    items = get_items(message)
    if items == 0:
        return 0
    items_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for i in items:
        item = types.KeyboardButton(i['title'])
        items_markup.add(item)

    return items_markup

def post_item(message):
    user_id = message.chat.id

    item_data["userId"] = user_id

    # POST-request for moktus.com
    url = "http://moktus.com/api/add-item"
    header = {"key": key}

    response = requests.post(url, headers=header, json=item_data)

    if response.status_code == 200:
        bot.send_message(user_id, "Ваша запись успешно опубликована на http://moktus.com", reply_markup=markup)
        log_message_generate(f"BOT sent to {user_id}: Ваша запись успешно опубликована на http://moktus.com \n")
    else:
        bot.send_message(user_id, f"Произошла ошибка во время отправки вашей записи. Код ошибки: {response.status_code}", reply_markup=markup)
        log_message_generate(f"BOT sent to {user_id}: Произошла ошибка во время отправки вашей записи. Код ошибки: {response.status_code} \n")
        print(f"ERROR WHILE POSTING! RESPONSE CODE IS: {response.status_code}, JSON RESPONSE IS: \n {response.json()}")

    # Log what user POST
    log_message_generate(f"User {user_id} POST: {item_data}")

    #Log response
    log_message_generate(f"SERVER answer code is: {response.status_code}")
    log_message_generate(f"SERVER json answer is: {response.text} \n")

def get_items(message):
    user_id = message.chat.id
    json = {"userId":user_id, 'limit':10, 'offset':0}

    url = "http://moktus.com/api/get-items"
    header = {"key": key}

    log_message_generate(f"USER {user_id} get items, json is: {json}")

    response = requests.post(url, headers=header, json=json)

    log_message_generate(f"SERVER json answer is: {response.json()}")
    log_message_generate(f"SERVER code answer is: {response.status_code} \n")

    if 'items' in response.json():
        user_items = response.json()['items']
    else:
        bot.send_message(user_id, f"Произошла ошибка при получении ваших записей, код ошибки: {response.status_code}")
        print(f"ERROR WHILE GETTING, RESPONSE CODE IS: {response.status_code}, JSON ANSWER IS: {response.json()}")
        return 0
    name_counts = {}

    for i in user_items:
        title = i['title']
        if title in name_counts:
            name_counts[title] += 1
            i['title'] = f"{title} ({name_counts[title]})"
        else:
            name_counts[title] = 1

    return user_items

def log_message(to_log_message):
    logs_dir = "logs"
    max_file_size = 1 * 1024 * 1024  # 1 MB
    max_logs = 5

    # Make directory of logs, if this dir don't exist
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Check current logs
    log_files = sorted(
        [f for f in os.listdir(logs_dir) if f.startswith("log")],
        key=lambda x: int(x[3:].split('.')[0] or 1)
    )

    # If logs more than 5, we rewrite first log
    if len(log_files) > max_logs:
        os.remove(os.path.join(logs_dir, log_files[0]))
        log_files.pop(0)

    # Check current file for writing
    if log_files:
        current_log = log_files[-1]
    else:
        current_log = "log1.txt"

    log_path = os.path.join(logs_dir, current_log)

    # Check size of current log
    if os.path.exists(log_path) and os.path.getsize(log_path) >= max_file_size:
        log_number = int(current_log[3:].split('.')[0] or 1) + 1
        current_log = f"log{log_number}.txt"
        log_path = os.path.join(logs_dir, current_log)

    # Writing message into log
    with open(log_path, "a") as log_file:
        log_file.write(to_log_message + "\n")

def log_message_generate(to_log_message):
    timezone = pytz.timezone("Europe/Riga")
    current_time = datetime.now(timezone)

    log_message(f"[{current_time}]" + to_log_message)

bot.infinity_polling()



