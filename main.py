from get_q_index import getQ
from bot import bot_auroraQI, send_message
from psql import get_users
import threading
import schedule
import time

# уведомления
def notifications():
    schedule.every(15).minutes.do(AuroraPossible)
    while True:
        schedule.run_pending()
        time.sleep(1)  # сейчас интервал 1 секунда

# функция проверяет значения индекса Q и присылает уведомления в зависимости от выбора пользователя
def AuroraPossible():
    Q = getQ()
    text = "Внимание значение Q велико, возможно Северное сияние. Q-индекс: "+str(Q)
    for i in range(5, 10):
        if Q >= i:
            joinedUsers = get_users(i)
            if joinedUsers:
                for user in joinedUsers:
                    send_message(user, text)

if __name__ == '__main__':
    t1 = threading.Thread(target=bot_auroraQI)
    t2 = threading.Thread(target=notifications)
    t1.start()
    t2.start()
    t1.join()
    t2.join()