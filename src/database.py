import sqlite3
from config import database_file

# Декоратор для работы с базой данных
def job_database(func):
    def wrapper(*args, **kwargs):
        try:
            conn = sqlite3.connect(database_file)
            c = conn.cursor()
            result = func(c, *args, **kwargs)
            if result == 'edit':
                conn.commit()
        except sqlite3.Error as e:
            print("Ошибка при работе с базой данных SQLite:", e)
        finally:
            if conn:
                conn.close()
        return result
    return wrapper

# Создаем таблицу
@job_database
def create_table(cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    status INTEGER NOT NULL default 1)''')
    return 'edit'

# Добавляем нового пользователя
@job_database
def add_user(cursor, username, password, role):
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
    return 'edit'

# Получить роль пользователя
@job_database
def get_role_user(cursor, username, password = None):
    if password:
        cursor.execute("SELECT role FROM users WHERE username=? and password=?", (username, password))
    else:
        cursor.execute("SELECT role FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    return result[0] if result else None

# Получить список пользователей
@job_database
def get_all_username(cursor):
    cursor.execute("SELECT username, password FROM users")
    users = cursor.fetchall()
    return users


@job_database
def get_count_users(cursor):
    cursor.execute("SELECT count(1) FROM users")
    users = cursor.fetchone()
    return users[0]