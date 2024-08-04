from database import *
from telebot import types, TeleBot
from server import delete_session, get_all_processes, write_users_to_file
from prettytable import PrettyTable

admin_button = [
    'Дать доступ пользователю TG',
    'Заблокировать пользователя TG',
    'Добавить пользователя VPN',
    'Разблокировать пользователя VPN',
    'Заблокировать пользователя VPN',
    'Удалить все сессии',
    'Посмотреть текущие сессии',
    'Посмотреть пользователей TG',
    'Посмотреть пользователей VPN'
]
user_button = [
    'Посмотреть свои аккаунты',
    'Привязать аккаунт',
    'Отвязать аккаунт',
    'Удалить свои сессии'
]


def start_program():
    create_table()
    create_table_bot()


def check_tg_usr(bot: TeleBot, message: types.Message):
    if message.from_user.is_bot:
        bot.send_message(message.chat.id,"Доступ запрещен")
        return False
    if not get_count_users():
        msg = bot.send_message(message.chat.id,"Пользователей нет в системе, Давайте добавим нового пользователя: выберите пользователя которого добавляем")
        bot.register_next_step_handler(msg, next_step, bot, 'first_user')
        return False
    if not check_enable_user(message.chat.id, message.from_user.username):
        bot.send_message(message.chat.id,"Вам запрещен доступ к возможностям бота, напишите администратору для разблокировки")
        return False
    return True


def next_step(message: types.Message, bot: TeleBot, type: str, role: str = None, *args):
    if not get_count_users() and type == 'first_user':
        add_tg_user(message.chat.id, message.from_user.username, 'admin', 1)
        bot.send_message(message.chat.id,"Администратор добавлен в систему")
        return
    if not check_tg_usr(bot, message):
        return
    if role == 'admin' and type in ('unlock_tg', 'lock_tg'):
        if message.text == 'Отмена':
            bot.send_message(message.chat.id, 'Доступные команды', reply_markup=get_markup(role))
        res = enable_user_tg(message.text, 1) if type == 'unlock_tg' else enable_user_tg(message.text, 0)
        if res == 'edit':
            msg = 'разблокирован' if type == 'unlock_tg' else 'заблокирован'
            bot.send_message(message.chat.id, f"Пользователь {msg}", reply_markup=get_markup(role))
            msg = "Вам дали доступ к боту" if type == 'unlock_tg' else "Вам ограничили доступ к боту"
            for usr in get_all_tg_username(message.text, 1):
                bot.send_message(usr[0], msg, reply_markup=get_markup(usr[2]))
        else:
            msg = 'разблокировке' if type == 'unlock_tg' else 'блокировке'
            bot.send_message(message.chat.id, f"Ошибка при {msg} пользователя", reply_markup=get_markup(role))
        return
    if role == 'admin' and type in ('unlock_vpn', 'lock_vpn'):
        if message.text == 'Отмена':
            bot.send_message(message.chat.id, 'Доступные команды', reply_markup=get_markup(role))
            return
        res = enable_user_vpn(message.text, 1) if type == 'unlock_vpn' else enable_user_vpn(message.text, 0)
        if res == 'edit':
            write_users_to_file([(el[0], el[1]) for el in get_all_username_vpn(enabled=1)])
            msg = 'разблокирован' if type == 'unlock_vpn' else 'заблокирован'
            bot.send_message(message.chat.id, f"Пользователь {msg}", reply_markup=get_markup(role))
        else:
            msg = 'разблокировке' if type == 'unlock_vpn' else 'блокировке'
            bot.send_message(message.chat.id, f"Ошибка при {msg} пользователя", reply_markup=get_markup(role))
        return
    if role == 'admin' and type == 'add_vpn_login':
        if message.text == 'Отмена':
            bot.send_message(message.chat.id, 'Доступные команды', reply_markup=get_markup(role))
            return
        for el in get_all_username():
            if el[0] == message.text:
                markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1=types.KeyboardButton('Отмена')
                markup.add(item1)
                msg = bot.send_message(message.chat.id, 'Такой пользователь уже существует. Введите имя нового пользователя', reply_markup=markup)
                bot.register_next_step_handler(msg, next_step, bot, 'add_vpn_login', role)
                return
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1=types.KeyboardButton('Отмена')
        markup.add(item1)
        msg = bot.send_message(message.chat.id, 'Введите пароль для пользователя', reply_markup=markup)
        bot.register_next_step_handler(msg, next_step, bot, 'add_vpn_password', role, message.text)
        return
    if role == 'admin' and type == 'add_vpn_password':
        if message.text == 'Отмена':
            bot.send_message(message.chat.id, 'Доступные команды', reply_markup=get_markup(role))
        else:
            add_user(args[0], message.text, 'user')
            write_users_to_file([(el[0], el[1]) for el in get_all_username_vpn(enabled=1)])
            for el in get_all_username(message.text):
                bot.send_message(message.chat.id, 'Пользователь создан', reply_markup=get_markup(role))
                break
            else:
                bot.send_message(message.chat.id, 'Пользователь не создан', reply_markup=get_markup(role))
        return
    if type == 'connect_vpn_login':
        if message.text == 'Отмена':
            bot.send_message(message.chat.id, 'Доступные команды', reply_markup=get_markup(role))
            return
        for el in get_my_account(message.chat.id):
            if el[0] == message.text:
                markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1=types.KeyboardButton('Отмена')
                markup.add(item1)
                msg = bot.send_message(message.chat.id, 'Данный аккаунт уже привязан к вам', reply_markup=markup)
                bot.register_next_step_handler(msg, next_step, bot, 'connect_vpn_login', role)
                return
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1=types.KeyboardButton('Отмена')
        markup.add(item1)
        msg = bot.send_message(message.chat.id, 'Введите пароль для пользователя', reply_markup=markup)
        bot.register_next_step_handler(msg, next_step, bot, 'connect_vpn_password', role, message.text)
        return
    if type == 'connect_vpn_password':
        if message.text == 'Отмена':
            bot.send_message(message.chat.id, 'Доступные команды', reply_markup=get_markup(role))
        else:
            for el in get_all_username():
                if el[0] == args[0] and el[1] == message.text:
                    if connect_tg_vpn(message.chat.id, args[0]) == 'edit':
                        bot.send_message(message.chat.id, 'Аккаунт привязан к вам', reply_markup=get_markup(role))
                    else:
                        bot.send_message(message.chat.id, 'Ошибка привязки аккаунта', reply_markup=get_markup(role))
                    return
        return
    if type == 'unconnect':
        accounts = get_my_account(message.chat.id)
        if not len(accounts):
            bot.send_message(message.chat.id,"Нечего отвязывать", reply_markup=get_markup(role))
            return
        for el in accounts:
            if el[0] == message.text:
                if unconnect_user(message.chat.id, el[0]) == 'edit':
                    bot.send_message(message.chat.id, "Аккаунт отвязан")
                else:
                    bot.send_message(message.chat.id, "Ошибка отвязки аккаунта")
                break
        else:
            bot.send_message(message.chat.id, "Такого аккаунта нет в привязанных")
        bot.send_message(message.chat.id, 'Доступные команды', reply_markup=get_markup(role))
    if type == 'del_ses_usr':
        if message.text == 'Отмена':
            bot.send_message(message.chat.id, 'Доступные команды', reply_markup=get_markup(role))
            return
        for el in get_my_account(message.chat.id):
            if message.text == 'Все':
                delete_session(el[0])
            elif el[0] == message.text:
                if delete_session(el[0]):
                    bot.send_message(message.chat.id, f'Все сессии {el[0]} удалены', reply_markup=get_markup(role))
                else:
                    bot.send_message(message.chat.id, f'Ошибка удаления {el[0]} сессий', reply_markup=get_markup(role))
                break
        else:
            if message.text == 'Все':
                bot.send_message(message.chat.id, 'Все привязанные сессии удалены', reply_markup=get_markup(role))
            else:
                bot.send_message(message.chat.id, 'Такого пользователя нет в привязанных', reply_markup=get_markup(role))


def check_enable_user(user_id, username):
    enabled = get_enable_user(user_id)
    if enabled is None:
        add_tg_user(user_id, username, 'user', 0)
        return False
    elif enabled == 1:
        return True
    return False


def get_markup(role: str):
    markup=types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    row = []
    if role == 'admin':
        for el in admin_button:
            item1=types.KeyboardButton(el)
            row.append(item1)
    for el in user_button:
        item1=types.KeyboardButton(el)
        row.append(item1)
    markup.add(*row)
    return markup


def get_table_str(head: list, data: list):
    table = PrettyTable()
    table.field_names = head  # Установка заголовков столбцов
    for row in data:
        table.add_row(row)
    return f"<pre>{table}</pre>"


def check_button(bot: TeleBot, message: types.Message, role: str):
    if role == 'admin' and message.text == "Дать доступ пользователю TG":
        blocked = get_all_tg_username(enabled=0)
        if not len(blocked):
            bot.send_message(message.chat.id,"Заблокированных пользователей нет", reply_markup=get_markup(role))
            return
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        row = []
        for usr in blocked:
            item1=types.KeyboardButton(usr[1])
            row.append(item1)
        item1=types.KeyboardButton('Отмена')
        row.append(item1)
        markup.add(*row)
        msg = bot.send_message(message.chat.id, 'Выберите пользователя для разблокировки', reply_markup=markup)
        bot.register_next_step_handler(msg, next_step, bot, 'unlock_tg', role)
        return
    if role == 'admin' and message.text == 'Заблокировать пользователя TG':
        users = get_all_tg_username(enabled=1)
        if not len(users):
            bot.send_message(message.chat.id,"Пользователей нет", reply_markup=get_markup(role))
            return
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        row = []
        for usr in users:
            item1=types.KeyboardButton(usr[1])
            row.append(item1)
        item1=types.KeyboardButton('Отмена')
        row.append(item1)
        markup.add(*row)
        msg = bot.send_message(message.chat.id, 'Выберите пользователя для блокировки', reply_markup=markup)
        bot.register_next_step_handler(msg, next_step, bot, 'lock_tg', role)
        return
    if role == 'admin' and message.text == 'Добавить пользователя VPN':
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1=types.KeyboardButton('Отмена')
        markup.add(item1)
        msg = bot.send_message(message.chat.id, 'Введите имя нового пользователя', reply_markup=markup)
        bot.register_next_step_handler(msg, next_step, bot, 'add_vpn_login', role)
        return
    if role == 'admin' and message.text in ('Заблокировать пользователя VPN', 'Разблокировать пользователя VPN'):
        if message.text == 'Заблокировать пользователя VPN':
            users = get_all_username_vpn(1)
        else:
            users = get_all_username_vpn(0)
        if not len(users):
            bot.send_message(message.chat.id,"Пользователей нет", reply_markup=get_markup(role))
            return
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        row = []
        for usr in users:
            item1=types.KeyboardButton(usr[0])
            row.append(item1)
        item1=types.KeyboardButton('Отмена')
        row.append(item1)
        markup.add(*row)
        msg = bot.send_message(message.chat.id, 'Выберите пользователя для блокировки', reply_markup=markup)
        if message.text in 'Заблокировать пользователя VPN':
            bot.register_next_step_handler(msg, next_step, bot, 'lock_vpn', role)
        else:
            bot.register_next_step_handler(msg, next_step, bot, 'unlock_vpn', role)
        return
    if role == 'admin' and message.text == 'Удалить все сессии':
        if delete_session():
            bot.send_message(message.chat.id, 'Все сессии удалены', reply_markup=get_markup(role))
        else:
            bot.send_message(message.chat.id, 'Ошибка удаления сессий', reply_markup=get_markup(role))
        return
    if role == 'admin' and message.text == 'Посмотреть текущие сессии':
        data = get_all_processes()
        if not len(data):
            bot.send_message(message.chat.id, 'Список сессий пуст', reply_markup=get_markup(role))
            return
        table_str = get_table_str(['PID', 'Local IP', 'Name'], data)
        bot.send_message(message.chat.id, table_str, parse_mode="HTML", reply_markup=get_markup(role))
        return
    if role == 'admin' and message.text == 'Посмотреть пользователей TG':
        data = get_all_tg_username()
        if not len(data):
            bot.send_message(message.chat.id, 'Список пользователей пуст', reply_markup=get_markup(role))
            return
        table_str = get_table_str(['USR_ID', 'NAME', 'ROLE', 'ENABLED'], data)
        bot.send_message(message.chat.id, table_str, parse_mode="HTML", reply_markup=get_markup(role))
        return
    if role == 'admin' and message.text == 'Посмотреть пользователей VPN':
        data = get_all_username_vpn()
        if not len(data):
            bot.send_message(message.chat.id, 'Список пользователей пуст', reply_markup=get_markup(role))
            return
        table_str = get_table_str(['USR', 'PASSWORD', 'STATUS'], data)
        bot.send_message(message.chat.id, table_str, parse_mode="HTML", reply_markup=get_markup(role))
        return
    if message.text == 'Посмотреть свои аккаунты':
        data = get_my_account(message.chat.id)
        if not len(data):
            bot.send_message(message.chat.id, 'У вас нет аккаунтов', reply_markup=get_markup(role))
            return
        table_str = get_table_str(['USR', 'PASSWORD'], data)
        bot.send_message(message.chat.id, table_str, parse_mode="HTML", reply_markup=get_markup(role))
        return
    if message.text == 'Привязать аккаунт':
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1=types.KeyboardButton('Отмена')
        markup.add(item1)
        msg = bot.send_message(message.chat.id, 'Введите логин вашего пользователя', reply_markup=markup)
        bot.register_next_step_handler(msg, next_step, bot, 'connect_vpn_login', role)
        return
    if message.text == 'Отвязать аккаунт':
        accounts = get_my_account(message.chat.id)
        if not len(accounts):
            bot.send_message(message.chat.id,"Нечего отвязывать", reply_markup=get_markup(role))
            return
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
        row = []
        for usr in accounts:
            item1=types.KeyboardButton(usr[0])
            row.append(item1)
        item1=types.KeyboardButton('Отмена')
        row.append(item1)
        markup.add(*row)
        msg = bot.send_message(message.chat.id, 'Выберите аккаунт для отвязки', reply_markup=markup)
        bot.register_next_step_handler(msg, next_step, bot, 'unconnect', role)
        return
    if message.text == 'Удалить свои сессии':
        data = get_my_account(message.chat.id)
        if not len(data):
            bot.send_message(message.chat.id, 'У вас нет аккаунтов', reply_markup=get_markup(role))
            return
        markup=types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        row = []
        for el in data:
            item1=types.KeyboardButton(el[0])
            row.append(item1)
        item1=types.KeyboardButton('Все')
        row.append(item1)
        item1=types.KeyboardButton('Отмена')
        row.append(item1)
        markup.add(*row)
        msg = bot.send_message(message.chat.id, 'Выбирете аккаунт для которого необходимо сбросить сессии', reply_markup=markup)
        bot.register_next_step_handler(msg, next_step, bot, 'del_ses_usr', role)
        return
    bot.send_message(message.chat.id, 'Иди подальше', reply_markup=get_markup(role))

