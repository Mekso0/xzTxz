
import telebot
import os
import logging
from telebot import types
from secrets import token_hex
from settings import API_TOKEN, stat, time, capt, kanal  # Не забудьте создать settings.py
import datetime

logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot(API_TOKEN)

admin_ids = [6646133212]
ADMIN_ID = 6646133212  # <--- Замените на ID вашего администратора
subscribers = []

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


@bot.message_handler(commands=['ban'])
def ban(message):
    # Проверяем, что команду использует администратор
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, " нет прав на использование этой команды")
        return
    try:
        user_id_to_ban = int(message.text.split(" ")[1])
        ban_user(user_id_to_ban)
        bot.reply_to(message, f"Пользователь с ID {user_id_to_ban} был заблокирован.")
    except (IndexError, ValueError):
        bot.reply_to(message, "Неверный формат команды. Используйте: /ban ID_пользователя")


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    if is_user_banned(user_id):
        bot.reply_to(message, "ты забанен в боте")
        return
    
    # Добавление пользователя в список подписчиков
    if user_id not in subscribers:
        subscribers.append(user_id)

    add_user_to_database(user_id, username)
    log_user_action(message, "Использовал команду /start")

    kb = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton(text="🏮Начать", callback_data="start")
    kb.add(button)

    global cached_welcome_image
    if cached_welcome_image:
        try:
            bot.send_photo(message.chat.id, cached_welcome_image, caption=stat, reply_markup=kb)
        except Exception as e:
            bot.send_message(message.chat.id, stat, reply_markup=kb)
            logging.error(f"Ошибка при отправке изображения из кэша: {e}")
    else:
        try:
            with open(WELCOME_IMAGE, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=stat, reply_markup=kb)
        except FileNotFoundError:
            bot.send_message(message.chat.id, stat, reply_markup=kb)
            logging.error(f"Файл изображения '{WELCOME_IMAGE}' не найден.")
        except Exception as e:
            bot.send_message(message.chat.id, stat, reply_markup=kb)
            logging.error(f"Ошибка при отправке изображения: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "start")
def start_callback(call):
    if is_user_banned(call.from_user.id):
        bot.answer_callback_query(call.id, "тв заблокированы в боте.", show_alert=True)
        return
    log_user_action(call.message, "Нажал кнопку 'Начать'")
    
    # Удаляем старое сообщение
    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        logging.error(f"Ошибка при удалении сообщения: {e}")
    
    # Создаем и отправляем новое сообщение
    kb2 = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(text="🏮Палитра цветов", url="https://g.co/kgs/KDTzamf")
    kb2.add(url_button)
    bot.send_message(chat_id=call.message.chat.id, text="❕Используй /timecyc низнеба, верхнеба, облака, цвет солнца к примеру⬇️\n /timecyc #FFFFFF #FFFFFF #FFFFFF #FFF000 Используй палитру цветов которая представлена ниже", reply_markup=kb2)
    
@bot.message_handler(commands=['unban'])
def unban(message):
    # Проверяем, что команду использует администратор
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ ты не админ")
        return
    try:
        user_id_to_unban = int(message.text.split(" ")[1])
        unban_user(user_id_to_unban)
        bot.reply_to(message, f"пользователь с ID {user_id_to_unban} был разбанен")
    except (IndexError, ValueError):
        bot.reply_to(message, "🙈 неверный формат команды. Используй /unban id чела\nтупой")


def unban_user(user_id):
    try:
        with open(BANNED_FILE, "r", encoding="utf-8") as f:
            banned_users = set(line.strip() for line in f)
        
        if str(user_id) in banned_users:
            banned_users.remove(str(user_id))
            with open(BANNED_FILE, "w", encoding="utf-8") as f:
                for uid in banned_users:
                    f.write(f"{uid}\n")
            logging.info(f"пользователь {user_id} был разбанен")
        else:
            logging.info(f"пользователь {user_id} не найден в заблокированных")
    except Exception as e:
        logging.error(f"ошибка при разблокировке {e}")

@bot.message_handler(commands=['setadm'])
def set_admin(message):
    if message.from_user.id not in ADMIN_IDS:  # Проверяем, является ли пользователь администратором
        bot.reply_to(message, "❌ ты не админ ")
        return
    try:
        new_admin_id = int(message.text.split(" ")[1])
        ADMIN_IDS.add(new_admin_id)  # Добавляем нового администратора
        bot.reply_to(message, f"Пользователь с ID {new_admin_id} стал администратором.")
        logging.info(f"Пользователь {new_admin_id} назначен администратором.")
    except (IndexError, ValueError):
        bot.reply_to(message, "Неверный формат команды. Используйте: /setadm ID_пользователя")


@bot.message_handler(commands=['whoami'])
def who_am_i(message):
    if message.from_user.id in ADMIN_IDS:
        bot.reply_to(message, f"Вы администратор (ID: {message.from_user.id}).")
    else:
        bot.reply_to(message, f"Вы обычный пользователь (ID: {message.from_user.id}).")
        
@bot.message_handler(commands=['public'])
def handle_public(message):
    if message.chat.id in admin_ids:
        bot.send_message(message.chat.id, "отправь твое текстовое сообщение, фото или GIF для рассылки.")
        bot.register_next_step_handler(message, send_to_all)
    else:
        bot.send_message(message.chat.id, "❌ ты не админ")

def send_to_all(message):
    if message.content_type == 'text':
        for subscriber in subscribers:
            bot.send_message(subscriber, message.text)
    elif message.content_type == 'photo':
        for subscriber in subscribers:
            bot.send_photo(subscriber, message.photo[-1].file_id, caption=message.caption)
    elif message.content_type == 'animation':  # Поддержка GIF
        for subscriber in subscribers:
            bot.send_animation(subscriber, message.animation.file_id, caption=message.caption)

    bot.send_message(message.chat.id, "Сообщение, фото или GIF отправлено всем подписчикам.")
        
@bot.message_handler(commands=['timecyc'])
def timecyc(message):
    if is_user_banned(message.from_user.id):
        bot.reply_to(message, "Вы заблокированы в боте.")
        return
    log_user_action(message, "Использовал команду /timecyc")
    timka = str(message.text)
    if len(timka) < 35:
        kb = types.InlineKeyboardMarkup()
        url_button = types.InlineKeyboardButton(text="🏮Палитра цветов", url="https://g.co/kgs/KDTzamf")
        kb.add(url_button)
        bot.send_message(message.chat.id, time, reply_markup=kb)
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
        bot.reply_to(message, "Неверный формат цвета. Используйте шестнадцатеричный формат (например, #RRGGBB).")
        return
    try:
        with open('debug/script.scm', 'r') as file:
            data = file.read()
            data = data.replace('skbr', str(colors[0][0])).replace('skbg', str(colors[0][1])).replace('skbb', str(colors[0][2])).replace('sktr', str(colors[1][0])).replace('sktg', str(colors[1][1])).replace('sktb', str(colors[1][2])).replace('scr', str(colors[2][0])).replace('scg', str(colors[2][1])).replace('scb', str(colors[2][2])).replace('clr', str(colors[3][0])).replace('clg', str(colors[3][1])).replace('clb', str(colors[3][2]))
            with open(grn1, 'w') as file:
                file.write(data)

            bot.send_document(message.chat.id, open(grn1, 'rb'), caption='Твой timecyc успешно создан🌴')
    except FileNotFoundError:
        bot.reply_to(message, "Файл 'debug/script.scm' не найден.")
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")

# Добавляем обработчик для команды /base
@bot.message_handler(commands=['base'])
def send_database(message):
    # Проверяем, является ли отправитель администратором
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "У вас нет прав на использование этой команды.")
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
bot.polling(timeout=3)
