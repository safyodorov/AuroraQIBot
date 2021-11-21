from PIL import Image
import requests
import telebot
import threading
import schedule
import time
import psycopg2
from config import *

# база данных телеграм пользователей
db_connection = psycopg2.connect(DB_URI, sslmode="require")
db_object = db_connection.cursor()

# функция парсит картинку, сохраняет ей, обрезает и сохраняет сновая под тем же именем
def getImage():
    url = 'https://www2.irf.se/maggraphs/preliminary_k_index_last_24.png'
    # запись файла на диск
    filename = 'Q-index.png'
    r = requests.get(url, allow_redirects=True)
    open(filename, 'wb').write(r.content)
    im = Image.open('Q-index.png')
    im.LOAD_TRUNCATED_IMAGES = True
    im.crop((608, 8, 1206, 306)).save('Q-index.png')

# функция возвращает значение Q-индекса
def getQ():
    getImage()

    im = Image.open('Q-index.png')
    im.LOAD_TRUNCATED_IMAGES = True
    # шаг на графике 14 пикселей
    # определяем значение Q-индекса
    # координаты пикселя, если Q = 1
    x = 577.5
    y = 142
    # шаг на графике
    delta = 14

    Q = 0
    while Q <= 9:
        r, g, b = im.getpixel((x, y))
        sum = r+g+b
        if sum > 649:
            break
        else:
            y -= delta
            Q += 1
    return Q

# клавиатура telegram вывел отдельно
def keyboard():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text='Узнать Q-индекс', callback_data="index"))
    markup.add(telebot.types.InlineKeyboardButton(text='Получить график', callback_data="picture"))
    markup.add(telebot.types.InlineKeyboardButton(text='Настроить уведомления', callback_data="notifications"))
    markup.add(telebot.types.InlineKeyboardButton(text='About', callback_data="about"))
    return markup

def keyboardnotes():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text='Не получать уведомления', callback_data="qset0"))
    markup.add(telebot.types.InlineKeyboardButton(text='Сообщать когда Q-индекс = 5', callback_data="qset5"))
    markup.add(telebot.types.InlineKeyboardButton(text='Сообщать когда Q-индекс = 6', callback_data="qset6"))
    markup.add(telebot.types.InlineKeyboardButton(text='Сообщать когда Q-индекс = 7', callback_data="qset7"))
    markup.add(telebot.types.InlineKeyboardButton(text='Сообщать когда Q-индекс = 8', callback_data="qset8"))
    markup.add(telebot.types.InlineKeyboardButton(text='Сообщать когда Q-индекс = 9', callback_data="qset9"))
    markup.add(telebot.types.InlineKeyboardButton(text='About', callback_data="about"))
    return markup


# telegram bot
bot = telebot.TeleBot(BOT_TOKEN)

# собираю список юзеров в базе данных
@bot.message_handler(commands=['start'])
def start(message):
    id = message.chat.id
    username = message.from_user.username

    db_object.execute(f"SELECT id FROM users WHERE id = {id}")
    result = db_object.fetchone()

    if not result:
        db_object.execute("INSERT INTO users(id, username, qset) VALUES(%s, %s, %s)", (id, username, 0))
        db_connection.commit()

    markup = keyboard()
    bot.send_message(message.chat.id, text="Привет, чем могу помочь?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    id = call.message.chat.id
    if call.data == "index":
        Q = getQ()
        bot.send_message(call.message.chat.id, "Привет, Q-индекс: "+str(Q))
    elif call.data == "picture":
        getImage()
        bot.send_photo(call.message.chat.id, open('Q-index.png', 'rb'))
    elif call.data == "about":
        bot.send_message(call.message.chat.id, 'AuroraQIBot v.1\n'
                                               '\n'
                                               'Бот получает онлайн-данные с магнитометров, расположенных в городе Кируна (Швеция)\n'
                                               'сайт: https://www2.irf.se/Observatory/?link[Magnetometers]=Data/\n'
                                               '\n'
                                               'Бот позволяет по запросу получить:\n'
                                               '– актуальное значение Q-индекса;\n'
                                               '– график изменения Q-индекса за последние сутки.\n'
                                               '\n'
                                               'Главная особенность этого бота:\n'
                                               'настраиваемые уведомления пользователей о значениях Q-индекса.')

    elif call.data == "notifications":
        markup = keyboardnotes()
        bot.send_message(call.message.chat.id, "Хорошо", reply_markup=markup)
    elif call.data == "qset0":
        db_object.execute(f"UPDATE users SET qset = 0 WHERE id = {id}")
        db_connection.commit()
        bot.send_message(call.message.chat.id, 'Уведомления отключены')
    elif call.data == "qset5":
        db_object.execute(f"UPDATE users SET qset = 5 WHERE id = {id}")
        db_connection.commit()
        bot.send_message(call.message.chat.id, 'Буду присылать уведомления, когда Q-индекс будет >=5. Cияние видно на широте 62° (г. Петрозаводск).')
    elif call.data == "qset6":
        db_object.execute(f"UPDATE users SET qset = 6 WHERE id = {id}")
        db_connection.commit()
        bot.send_message(call.message.chat.id, 'Буду присылать уведомления, когда Q-индекс будет >=6. Сияние видно на широте 60° (г. Санкт-Петербург).')
    elif call.data == "qset7":
        db_object.execute(f"UPDATE users SET qset = 7 WHERE id = {id}")
        db_connection.commit()
        bot.send_message(call.message.chat.id, 'Буду присылать уведомления, когда Q-индекс будет >=7. Сияние видно на широте 56° (Иваново, Москва, Нижний Новгород, Казань, Екатеринбург, Новосибирск).')
    elif call.data == "qset8":
        db_object.execute(f"UPDATE users SET qset = 8 WHERE id = {id}")
        db_connection.commit()
        bot.send_message(call.message.chat.id, 'Буду присылать уведомления, когда Q-индекс будет >=8. Сияние видно на широте 52° (Самара, Курск, Липецк).')
    elif call.data == "qset9":
        db_object.execute(f"UPDATE users SET qset = 9 WHERE id = {id}")
        db_connection.commit()
        bot.send_message(call.message.chat.id, 'Буду присылать уведомления, когда Q-индекс будет >=9. Сияние видно на широте 50°–45° (Крым, Кавказ).')

@bot.message_handler(content_types=['text'])

def get_text_messages(message):

    if message.text == "ку" or message.text == "Ку" or message.text == "КУ" or message.text == "кУ":
        Q = getQ()
        bot.send_message(message.chat.id, "Привет, Q-индекс: "+str(Q))
    elif message.text == "график" or message.text == "График" or message.text == "ГРАФИК" or message.text == "гРАФИК":
        getImage()
        bot.send_photo(message.chat.id, open('Q-index.png', 'rb'))
    else:
        markup = keyboard()
        bot.send_message(message.chat.id, "Напишите: ку ИЛИ график. ИЛИ нажмите на кнопку ", reply_markup=markup)

# функция проверяет значения индекса Q и присылает пользователся уведомление при Q >= 6
def AuroraPossible():
    db_object = db_connection.cursor()
    Q = getQ()
    if Q >= 1:
        # запрашиваю из базы данных список юзеров cо значением qset = 5
        db_object.execute(f"SELECT id FROM users WHERE qset = 5")
        joineduser5 = db_object.fetchone()
        if joineduser5:
            for user in joineduser5:
                bot.send_message(user, "Внимание значение Q велико, возможно Северное сияние. Q-индекс: "+str(Q))
    elif Q >= 2:
        db_object.execute(f"SELECT id FROM users WHERE qset = 6")
        joineduser6 = db_object.fetchone()
        if joineduser6:
            for user in joineduser6:
                bot.send_message(user, "Внимание значение Q велико, возможно Северное сияние. Q-индекс: "+str(Q))
    elif Q >= 7:
        db_object.execute(f"SELECT id FROM users WHERE qset = 7")
        joineduser7 = db_object.fetchone()
        if joineduser7:
            for user in joineduser7:
                bot.send_message(user, "Внимание значение Q велико, возможно Северное сияние. Q-индекс: "+str(Q))
    elif Q >= 8:
        db_object.execute(f"SELECT id FROM users WHERE qset = 8")
        joineduser8 = db_object.fetchone()
        if joineduser8:
            for user in joineduser8:
                bot.send_message(user, "Внимание значение Q велико, возможно Северное сияние. Q-индекс: "+str(Q))
    elif Q >= 9:
        db_object.execute(f"SELECT id FROM users WHERE qset = 9")
        joineduser9 = db_object.fetchone()
        if joineduser9:
            for user in joineduser9:
                bot.send_message(user, "Внимание значение Q велико, возможно Северное сияние. Q-индекс: "+str(Q))

# этот момент до конца не понимаю, но код работает!
def notifications():
    schedule.every(2).minutes.do(AuroraPossible)

    while True:
        schedule.run_pending()
        time.sleep(1)  # сейчас интервал 1 секунда

if __name__ == '__main__':
    t1 = threading.Thread(target=bot.polling)
    t2 = threading.Thread(target=notifications, args=())
    t1.start()
    t2.start()
    t1.join()
    t2.join()