from telebot import telebot, types
from datetime import datetime
import pytz
import requests
import os

# pip install pyTelegramBotAPI
# pip install pytz
# pip install requests

# Get token from token.txt file
token_file = open('token.txt', 'r')
token = token_file.read().strip() # Remove
# print(f"Token: {token}")
token_file.close()

bot = telebot.TeleBot(token) # Set bot token

data = {} # Data for POST

# Get key from key.txt file
key_file = open('key.txt', 'r')
key = key_file.read().strip()
# print(f"Key: {key}")
key_file.close()

markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
add_item = types.KeyboardButton("Добавить запись")
markup.add(add_item)

# Start message
@bot.message_handler(commands=['start'])
def start_message(message):
    first_name = message.from_user.first_name  # Get user first name
    last_name = message.from_user.last_name  # Get user last name

    bot.send_message(
        message.chat.id,
        f"Добро пожаловать, {first_name} {last_name or ''}! Что вы бы хотели сделать?",
        reply_markup=markup
    )

@bot.message_handler(content_types=['text'])
def handle_messages(message):
    user_message = message.text  # Get the message text
    user_id = message.chat.id  # Get the user ID

    first_name = message.from_user.first_name  # Get user first name
    last_name = message.from_user.last_name  # Get user last name

    print(f"Пользователь {user_id} ({first_name} {last_name or ''}) отправил: {user_message}")

    if user_message == "Добавить запись":
        bot.send_message(user_id, "Введите название записи...")
        print("BOT: Введите название записи...")
        bot.register_next_step_handler(message, set_title, data)


def set_title(message, data):
    user_id = message.chat.id  # Get the user ID
    data["title"] = message.text # Add title

    bot.send_message(user_id, "Теперь опишите свою запись...")
    print("BOT: Теперь опишите свою запись...")

    bot.register_next_step_handler(message, set_descr, data)

def set_descr(message, data):
    user_id = message.chat.id # Get ther user ID
    data["descr"] = message.text # Get description

    bot.send_message(user_id, "Теперь напишите теги через запятую...(Если вы напишите их по-другому, теги могут быть отправленны не корректно.")
    print("BOT: Теперь напишите теги через запятую...")

    bot.register_next_step_handler(message, set_tags)

def set_tags(message):
    user_id = message.chat.id
    data["tags"] = message.text # Get tags

    bot.send_message(user_id, "Готово! Ваша запись была опубликована на http://moktus.com!")
    print("BOT: Готово! Ваша запись была опубликована на http://moktus.com!")

    post(message)

def post(message):
    user_id = message.chat.id

    data["user_id"] = user_id

    # POST-request for moktus.com
    url = "http://moktus.com/api/add-item"
    header = {"key": key}

    response = requests.post(url, headers=header, json=data)

    timezone = pytz.timezone("Europe/Riga")
    current_time = datetime.now(timezone)

    to_log_message = (f"[{current_time}] User {user_id} sends: {data} \n"
                      f"[{current_time}] Site response is: {response.text} \n")

    log_message(to_log_message)
# Log POST data
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


bot.infinity_polling()



