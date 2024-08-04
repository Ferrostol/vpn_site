import sqlite3
from config import database_file

# Декоратор для работы с базой данных
def job_database(func):
    def wrapper(*args, **kwargs):
        result = None
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






# ЛОКАЛЬНАЯ ВСТАВКА, у некоторых функций меняется функционал
@job_database
def create_table_bot(cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS tg_users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    enabled integer default 0,
                    role TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS tg_ls_usr_vpn
                    (tg_usr INTEGER REFERECES tg_users,
                    usr INTEGER REFERECES users)''')
    return 'edit'

@job_database
def get_count_users(cursor):
    cursor.execute("SELECT count(1) FROM tg_users")
    users = cursor.fetchone()
    return users[0]

@job_database
def add_tg_user(cursor, telegram_user_id, username, role, enabled):
    cursor.execute("INSERT INTO tg_users (telegram_user_id, username, role, enabled) VALUES (?, ?, ?, ?)", (telegram_user_id, username, role, enabled))
    return 'edit'

@job_database
def get_all_tg_username(cursor, username = None, enabled = None):
    cursor.execute("SELECT telegram_user_id, username, role, enabled FROM tg_users where (enabled = ? or ? is null) and (username = ? or ? is null)", (enabled, enabled, username, username))
    users = cursor.fetchall()
    return users

@job_database
def get_enable_user(cursor, user_id_chat):
    cursor.execute("SELECT enabled FROM tg_users WHERE telegram_user_id=?", (user_id_chat, ))
    result = cursor.fetchone()
    return result[0] if result else None

@job_database
def get_role_user(cursor, user_id_chat):
    cursor.execute("SELECT role FROM tg_users WHERE telegram_user_id=?", (user_id_chat, ))
    result = cursor.fetchone()
    return result[0] if result else None

@job_database
def enable_user_tg(cursor, username, enabled):
    cursor.execute("update tg_users set enabled = ? WHERE username=?", (enabled, username))
    return 'edit'

@job_database
def enable_user_vpn(cursor, username, enabled):
    cursor.execute("update users set status = ? WHERE username=?", (enabled, username))
    return 'edit'

@job_database
def get_my_account(cursor, user_id):
    cursor.execute("select u.username, u.password from tg_users tu, tg_ls_usr_vpn tluv, users u where tu.id = tluv.tg_usr and tluv.usr = u.id and tu.telegram_user_id = ?", (user_id,))
    users = cursor.fetchall()
    return users

@job_database
def connect_tg_vpn(cursor, usr_id, vpn_name):
    cursor.execute("insert into tg_ls_usr_vpn (tg_usr, usr) values ((select id from tg_users where telegram_user_id = ?), (select id from users where username = ?))", (usr_id, vpn_name))
    return 'edit'

@job_database
def unconnect_user(cursor, usr_id, vpn_name):
    cursor.execute("delete from tg_ls_usr_vpn where tg_usr = (select id from tg_users where telegram_user_id = ?) and usr = (select id from users where username = ?)", (usr_id, vpn_name))
    return 'edit'

@job_database
def get_all_username_vpn(cursor, enabled = None):
    cursor.execute("SELECT username, password, status FROM users where (status = ? or ? is null)", (enabled, enabled))
    users = cursor.fetchall()
    return users
