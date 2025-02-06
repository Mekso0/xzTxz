
import telebot
import os
import logging
from telebot import types
from secrets import token_hex
from settings import API_TOKEN, stat, time, capt, kanal  # Не забудьте создать settings.py
import datetime
import time

logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot(API_TOKEN, threaded=False) # Установили threaded=False

ADMIN_ID = 6646133212  # <--- Замените на ID вашего администратора
ADMIN_IDS = [6646133212] 

DATABASE_FILE = "database.txt"
BANNED_FILE = "banned.txt"
WELCOME_IMAGE = "welcome.png" # Имя файла изображения

conversations = {}
reklama_mode = False

# Кэшируем изображение при запуске
cached_welcome_image = None

# Функция для загрузки изображения в память
def load_welcome_image():
    global cached_welcome_image
    try:
        with open(WELCOME_IMAGE, 'rb') as photo:
           cached_welcome_image = photo.read()
           logging.info(f"Изображение '{WELCOME_IMAGE}' успешно загружено в память.")
    except FileNotFoundError:
        logging.error(f"Файл изображения '{WELCOME_IMAGE}' не найден.")
    except Exception as e:
        logging.error(f"Ошибка при загрузке изображения: {e}")


# Функция для безопасного добавления данных пользователя в базу данных, только один раз на пользователя
def add_user_to_database(user_id, username):
    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            existing_users = set(line.strip().split(',')[0] for line in f)
    except FileNotFoundError:
        existing_users = set()

    if str(user_id) not in existing_users:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(DATABASE_FILE, "a", encoding="utf-8") as f:
                f.write(f"{user_id},{username},{timestamp}\n")
            logging.info(f"Добавлен пользователь {user_id} ({username}) в базу данных в {timestamp}")
        except Exception as e:
            logging.error(f"Ошибка записи в базу данных: {e}")


def log_user_action(message, action):
    user = message.from_user.username if message.from_user.username else "Anonymous"
    chat_id = message.chat.id
    message_id = message.message_id
    conversations[chat_id] = {"user_id": message.from_user.id, "message_id": message_id}

    bot.send_message(ADMIN_ID, f"\nПользователь: {message.from_user.first_name} \nПрофиль: tg://openmessage?user_id={message.from_user.id} \nЮзер: @{user}\nДействие: {action} \nChat ID: {chat_id} \nMessage ID: {message_id}")


# Функция для проверки, заблокирован ли пользователь
def is_user_banned(user_id):
    try:
        with open(BANNED_FILE, "r", encoding="utf-8") as f:
            banned_users = set(line.strip() for line in f)
    except FileNotFoundError:
        banned_users = set()
    return str(user_id) in banned_users


# Функция для добавления пользователя в список заблокированных
def ban_user(user_id):
    try:
        with open(BANNED_FILE, "a", encoding="utf-8") as f:
            f.write(f"{user_id}\n")
        logging.info(f"Пользователь {user_id} заблокирован.")
    except Exception as e:
        logging.error(f"Ошибка при добавлении пользователя в список заблокированных: {e}")

# Функция для разблокировки пользователя
def unban_user(user_id):
    try:
        with open(BANNED_FILE, "r", encoding="utf-8") as f:
            banned_users = set(line.strip() for line in f)
        
        if str(user_id) in banned_users:
            banned_users.remove(str(user_id))
            with open(BANNED_FILE, "w", encoding="utf-8") as f:
                for user in banned_users:
                    f.write(f"{user}\n")
            logging.info(f"Пользователь {user_id} разблокирован.")
            return True
        else:
            logging.info(f"Пользователь {user_id} не был забанен.")
            return False
    except FileNotFoundError:
        logging.error("Файл со списком забаненных пользователей не найден.")
        return False
    except Exception as e:
        logging.error(f"Ошибка при разблокировке пользователя: {e}")
        return False

@bot.message_handler(commands=['ban'])
def ban(message):
    # Проверяем, что команду использует администратор
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, " 💀 Команда доступна только админам бота!")
        return
    try:
        user_id_to_ban = int(message.text.split(" ")[1])
        ban_user(user_id_to_ban)
        bot.reply_to(message, f"😓 Пользователь с айди {user_id_to_ban} был забанен!")
    except (IndexError, ValueError):
        bot.reply_to(message, "Неверный формат команды. Используйте: /ban ID_пользователя")

@bot.message_handler(commands=['unban'])
def unban(message):
    # Проверяем, что команду использует администратор
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "💀 Команда доступна только админам бота!")
        return
    try:
        user_id_to_unban = int(message.text.split(" ")[1])
        if unban_user(user_id_to_unban):
            bot.reply_to(message, f"🥳 Пользователь с айди {user_id_to_unban} был разбанен!")
        else:
            bot.reply_to(message, f"😔 Пользователь с айди {user_id_to_unban} не был забанен или произошла ошибка!")
    except (IndexError, ValueError):
        bot.reply_to(message, "Неверный формат команды. Используйте: /unban ID_пользователя")


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username    
    if is_user_banned(user_id):
        bot.reply_to(message, "❌ Ты забанен в боте!\nЗа причиной/разбаном @DazSky")
        return
    
    add_user_to_database(user_id, username)
    log_user_action(message, "Использовал команду /start")

    kb = types.InlineKeyboardMarkup()
    
    # Создаем кнопки в один ряд
    button1 = types.InlineKeyboardButton(text="TIMECYC", callback_data="TimeBrTime", parse_mode="HTML")
    button2 = types.InlineKeyboardButton(text="TIMECYC NEIZZIR", callback_data="nTimeBrTime", parse_mode="HTML")
    kb.add(button1, button2)  # Добавляем кнопки в один ряд
    
    global cached_welcome_image
    if cached_welcome_image:
        try:
            bot.send_photo(message.chat.id, cached_welcome_image, caption=stat, reply_markup=kb, parse_mode='Markdown')
        except Exception as e:
            bot.send_message(message.chat.id, stat, reply_markup=kb, parse_mode='Markdown')
            logging.error(f"Ошибка при отправке изображения из кэша: {e}")
    else:
        try:
            with open(WELCOME_IMAGE, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=stat, reply_markup=kb, parse_mode='Markdown')
        except FileNotFoundError:
            bot.send_message(message.chat.id, stat, reply_markup=kb, parse_mode='Markdown')
            logging.error(f"Файл изображения '{WELCOME_IMAGE}' не найден.")
        except Exception as e:
           bot.send_message(message.chat.id, stat, reply_markup=kb, parse_mode='Markdown')
           logging.error(f"Ошибка при отправке изображения: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "TimeBrTime")
def TimeBrTime_callback(call):
    if is_user_banned(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Ты забанен в боте!\nЗа причиной/разбаном @DazSky", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    log_user_action(call.message, "Нажал кнопку 'Создать TIMECYC'")
    
    # Удаляем старое сообщение
    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        logging.error(f"Ошибка при удалении сообщения: {e}")
    
    kb = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text="☁️ Палитра цветов", url="https://g.co/kgs/KDTzamf")
    kb.add(url_button)
    
    bot.send_message(call.message.chat.id,"☁️")
    
    bot.send_message(call.message.chat.id, "❕Используй /timecyc низнеба, верхнеба, облака, цвет солнца.\nК примеру:\n/timecyc #FF0000 #00FF00 #0000FF #FFFFFF\nИспользуй палитру цветов которая представлена ниже", reply_markup=kb)
    
@bot.callback_query_handler(func=lambda call: call.data == "nTimeBrTime")
def nTimeBrTime_callback(call):
    if is_user_banned(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Ты забанен в боте!\nЗа причиной/разбаном @DazSky", show_alert=True)
        return
    bot.answer_callback_query(call.id)
    log_user_action(call.message, "Нажал кнопку 'Создать TIMECYC для NEIZZIR'")
    
    # Удаляем старое сообщение
    try:
         bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        logging.error(f"Ошибка при удалении сообщения: {e}")

    kb = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text="☁️ Палитра цветов", url="https://g.co/kgs/KDTzamf")
    kb.add(url_button)
    
    bot.send_message(call.message.chat.id,"☁️")
       
    bot.send_message(call.message.chat.id, "❕Используй /ntimecyc низнеба, верхнеба, облака, цвет солнца, цвет солнца2. К примеру:\n/ntimecyc #FF0000 #00FF00 #0000FF #FFFFFF #FF0000\nИспользуй палитру цветов которая представлена ниже", reply_markup=kb)


@bot.message_handler(commands=['timecyc'])
def timecyc(message):
    if is_user_banned(message.from_user.id):
        bot.reply_to(message, "❌ Ты забанен в боте!\nЗа причиной/разбаном @DazSky")
        return
    log_user_action(message, "Использовал команду /timecyc")
    timka = str(message.text)
    if len(timka) < 35:
        kb = types.InlineKeyboardMarkup()
        url_button = types.InlineKeyboardButton(text="☁️ Палитра цветов", url="https://g.co/kgs/KDTzamf")
        kb.add(url_button)
        bot.send_message(message.chat.id,"☁️")
        bot.send_message(message.chat.id, "❕Используй /timecyc низнеба, верхнеба, облака, цвет солнца.\nК примеру:\n/timecyc #FF0000 #00FF00 #0000FF #FFFFFF\nИспользуй палитру цветов которая представлена ниже", reply_markup=kb)
        return
    code = token_hex(3)
    print(f"Создан файл it.{code}_timecyc.json")
    random_name = message.from_user.username
    grn1 = f"{code}_timecyc.json"
    usercs = str(message.text)
    usercs = usercs.lstrip('/timecyc ').replace('#', '').split()
    try:
        colors = [tuple(int(usercs[i][j:j + 2], 16) for j in (0, 2, 4)) for i in range(4)]
    except (IndexError, ValueError):
        bot.reply_to(message, "🤫 Неверный формат цвета!\nВот как правильно #RRGGBB")
        return
    try:
        with open('debug/script.scm', 'r') as file:
            data = file.read()
            data = data.replace('skbr', str(colors[0][0])).replace('skbg', str(colors[0][1])).replace('skbb', str(colors[0][2])).replace('sktr', str(colors[1][0])).replace('sktg', str(colors[1][1])).replace('sktb', str(colors[1][2])).replace('scr', str(colors[2][0])).replace('scg', str(colors[2][1])).replace('scb', str(colors[2][2])).replace('clr', str(colors[3][0])).replace('clg', str(colors[3][1])).replace('clb', str(colors[3][2]))
            with open(grn1, 'w') as file:
                file.write(data)

            bot.send_document(message.chat.id, open(grn1, 'rb'), caption='Твой timecyc успешно создан🏁')
    except FileNotFoundError:
        bot.reply_to(message, "Файл 'debug/script.scm' не найден.")
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")
        
@bot.message_handler(commands=['ntimecyc'])
def ntimecyc(message):
    if is_user_banned(message.from_user.id):
        bot.reply_to(message, "❌ Ты забанен в боте!\nЗа причиной/разбаном @DazSky")
        return
    log_user_action(message, "Использовал команду /ntimecyc")
    timka = str(message.text)
    if len(timka) < 35:
        kb = types.InlineKeyboardMarkup()
        url_button = types.InlineKeyboardButton(text="☁️ Палитра цветов", url="https://g.co/kgs/KDTzamf")
        kb.add(url_button)
        bot.send_message(message.chat.id,"☁️")
        bot.send_message(message.chat.id, " ❕Используй /ntimecyc низнеба, верхнеба, облака, цвет солнца, цвет солнца2. К примеру:\n/ntimecyc #FF0000 #00FF00 #0000FF #FFFFFF #FF0000\nИспользуй палитру цветов которая представлена ниже", reply_markup=kb)
        return
    code = token_hex(3)
    print(f"Создан файл it.{code}_timecyc.json")
    random_name = message.from_user.username
    grn1 = f"{code}_timecyc.json"
    usercs = str(message.text)
    usercs = usercs.lstrip('/ntimecyc ').replace('#', '').split()
    try:
         if len(usercs) < 4:
             bot.reply_to(message, "🧟 Недостаточно цветов! Необходимо 4 цвета в формате HEX")
             return
         colors = [tuple(int(usercs[i][j:j + 2], 16) for j in (0, 2, 4)) for i in range(4)]
    except (IndexError, ValueError):
        bot.reply_to(message, "🤫 Неверный формат цвета!\nВот как правильно #RRGGBB")
        return
    try:
        with open('debug/scripn.scm', 'r') as file:
            data = file.read()
            data = data.replace('sbr', str(colors[0][0])).replace('sbg', str(colors[0][1])).replace('sbb', str(colors[0][2])).replace('str', str(colors[1][0])).replace('stg', str(colors[1][1])).replace('stb', str(colors[1][2])).replace('scr', str(colors[2][0])).replace('scg', str(colors[2][1])).replace('scb', str(colors[2][2])).replace('clr', str(colors[3][0])).replace('clg', str(colors[3][1])).replace('clb', str(colors[3][2])).replace('sco', str(0)).replace('sca', str(0)).replace('srr', str(0))
            with open(grn1, 'w') as file:
                file.write(data)

            bot.send_document(message.chat.id, open(grn1, 'rb'), caption='Твой timecyc для лаунчера Neizzir успешно создан🏁')
    except FileNotFoundError:
        bot.reply_to(message, "Файл 'debug/scripn.scm' не найден.")
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")


# Добавляем обработчик для команды /base
@bot.message_handler(commands=['base'])
def send_database(message):
    # Проверяем, является ли отправитель администратором
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "💀 Команда доступна только админам бота!")
        return

    try:
        # Отправляем файл database.txt
        with open(DATABASE_FILE, 'rb') as f:
            bot.send_document(message.chat.id, f, caption="Файл базы данных")
        logging.info(f"Администратор {ADMIN_ID} запросил файл базы данных.")
    except FileNotFoundError:
        bot.reply_to(message, "Файл базы данных не найден.")
        logging.error("Файл базы данных не найден.")
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")
        logging.error(f"Ошибка при отправке файла базы данных: {e}")


@bot.message_handler(func=lambda message: True)  # Обрабатывает все остальные сообщения
def handle_other_messages(message):
    log_user_action(message, f"Написал сообщение: {message.text}")


@bot.message_handler(commands=['reklama'], func=lambda message: message.from_user.id == ADMIN_ID)
def start_reklama(message):
    global reklama_mode
    reklama_mode = True
    bot.reply_to(message, "Введите текст, фото или сообщение с кнопками для рассылки.")


@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and reklama_mode)
def send_reklama(message):
    global reklama_mode
    reklama_mode = False
    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as f:
            for line in f:
                user_id, username, timestamp = line.strip().split(',')
                try:
                    # Попытка отправить сообщение. Обрабатывает различные типы сообщений
                    if message.photo:
                        bot.send_photo(int(user_id), message.photo[-1].file_id, caption=message.caption)
                    elif message.text:
                        bot.send_message(int(user_id), message.text, parse_mode="HTML", reply_markup=message.reply_markup)
                    else:
                        bot.send_message(int(user_id), "Ошибка при отправке сообщения.")

                except Exception as e:
                    logging.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
        bot.reply_to(message, "Рассылка завершена.")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")


@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and message.text != "/reklama")  # Только сообщения от администратора, не /reklama
def handle_admin_message(message):
    if message.chat.id in conversations:
        chat_id = message.chat.id
        bot.send_message(chat_id, f"Ответ от администратора: {message.text}")
        del conversations[chat_id]

# Загружаем изображение при старте бота
load_welcome_image()

while True:
    try:
         bot.polling(none_stop=True, timeout=30)
    except Exception as e:
        logging.error(f"Ошибка при поллинге: {e}")
        time.sleep(10)
