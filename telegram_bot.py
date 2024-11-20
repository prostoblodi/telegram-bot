from telebot import telebot, types
import requests

# Get token from token.txt file
token_file = open('token.txt', 'r')
token = token_file.read().strip() # Remove
print(f"Token: {token}")
token_file.close()

bot = telebot.TeleBot(token) # Set bot token

title = '' # Announce title
descr = '' # Announce description
tags = '' # Announce tags

# Get key from key.txt file
key_file = open('key.txt', 'r')
key = key_file.read().strip()
print(f"Key: {key}")
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
        bot.register_next_step_handler(message, set_title)


def set_title(message):
    user_id = message.chat.id  # Get the user ID
    title = message.text # Get the title

    bot.send_message(user_id, "Теперь опишите свою запись...")
    print("BOT: Теперь опишите свою запись...")

    bot.register_next_step_handler(message, set_descr)

def set_descr(message):
    user_id = message.chat.id # Get ther user ID
    descr = message.text # Get description

    bot.send_message(user_id, "Теперь напишите теги через запятую...(Если вы напишите их по-другому, теги могут быть отправленны не корректно.")
    print("BOT: Теперь напишите теги через запятую...")

    bot.register_next_step_handler(message, set_tags)

def set_tags(message):
    user_id = message.chat.id
    tags = message.text # Get tags

    bot.send_message(user_id, "Готово! Ваша запись была опубликована на moktus.com!")
    print("BOT: Готово! Ваша запись была опубликована на moktus.com!")

    post(message)

def post(message):
    user_id = message.chat.id

    # POST-request for moktus.com
    url = "http://moktus.com/api/add-item"
    header = {"key": key}
    data = {
     "title": title,
     "descr": descr,
     "tags": tags,
     "user_id": user_id
    }
    print(f"Title: {title}, \n Description: {descr} \n Tags: {tags} \n User id: {user_id}")

    response = requests.post(url, headers=header, json=data)

    print(response.status_code)
    print(response.json())

bot.infinity_polling()



