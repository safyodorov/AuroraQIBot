import psycopg2
import os

# база данных телеграм пользователей
DB_URI = os.environ['DATABASE_URL']
db_connection = psycopg2.connect(DB_URI, sslmode="require")
db_object = db_connection.cursor()

# запрашиваю из базы данных список юзеров c определенным значением qset
def get_users(i):
    db_object.execute(f"SELECT id FROM users WHERE qset = {i}")
    joinedUsers = db_object.fetchone()
    return joinedUsers

def id_check(id, username):
    db_object.execute(f"SELECT id FROM users WHERE id = {id}")
    result = db_object.fetchone()

    if not result:
        db_object.execute("INSERT INTO users(id, username, qset) VALUES(%s, %s, %s)", (id, username, 0))
        db_connection.commit()

def id_write(id, data):
    db_object.execute(f"UPDATE users SET qset = {data} WHERE id = {id}")
    db_connection.commit()