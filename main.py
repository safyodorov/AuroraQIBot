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
    markup.add(telebot.types.InlineKeyboardButton(text='About', callback_data="about"))
    return markup


# telegram bot
bot = telebot.TeleBot(BOT_TOKEN)
# запрашиваю из базы данных список юзеров
db_object.execute(f"SELECT id FROM users")
joinedUser = db_object.fetchone()


# собираю список юзеров в базе данных
@bot.message_handler(commands=['start'])
def start(message):
    id = message.chat.id
    username = message.from_user.username

    db_object.execute(f"SELECT id FROM users WHERE id = {id}")
    result = db_object.fetchone()

    if not result:
        db_object.execute("INSERT INTO users(id, username, messages) VALUES(%s, %s, %s)", (id, username, 0))
        db_connection.commit()

    markup = keyboard()
    bot.send_message(message.chat.id, text="Привет, чем могу помочь?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):

    if call.data == "index":
        Q = getQ()
        bot.send_message(call.message.chat.id, "Привет, Q-индекс: "+str(Q))
    elif call.data == "picture":
        getImage()
        bot.send_photo(call.message.chat.id, open('Q-index.png', 'rb'))
    elif call.data == "about":
        bot.send_message(call.message.chat.id, 'AuroraQ6Bot v.1\n'
                                               '\n'
                                               'Бот получает онлайн-данные с магнитометров, расположенных в городе Кируна (Швеция)\n'
                                               'сайт: https://www2.irf.se/Observatory/?link[Magnetometers]=Data/\n'
                                               '\n'
                                               'Бот позволяет по запросу получить:\n'
                                               '– актуальное значение Q-индекса;\n'
                                               '– график изменения Q-индекса за последние сутки.\n'
                                               '\n'
                                               'Главная особенность этого бота:\n'
                                               'Уведомление пользователей о значениях Q-индекса равном 6 и более единицам. '
                                               'Именно при таких значениях возможно наблюдение северного сияния '
                                               'на широте 60° (Санкт-Петербург)')

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
def AuroraPossible(joinedUser):
    Q = getQ()
    if Q >= 6:
        for user in joinedUser:
            bot.send_message(user, "Внимание значение Q велико, возможно Северное сияние. Q-индекс: "+str(Q))

# этот момент до конца не понимаю, но код работает!
def notifications(joinedUser):
    schedule.every(15).minutes.do(AuroraPossible, joinedUser)
    while True:
        schedule.run_pending()
        time.sleep(1)  # сейчас интервал 1 секунда

if __name__ == '__main__':
    t1 = threading.Thread(target=bot.polling)
    t2 = threading.Thread(target=notifications, args=(joinedUser,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()