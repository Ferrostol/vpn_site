import re

from telebot import types, TeleBot
from prettytable import PrettyTable

from database import *
from buttons import *
from server import delete_session, get_all_processes, write_users_to_file



def start_program():
    create_table()
    create_table_bot()


def check_tg_usr(bot: TeleBot, message: types.Message):
    if not get_count_users():
        msg = bot.send_message(message.chat.id,
                               "Пользователей нет в системе, Давайте добавим нового пользователя: выберите "
                               "пользователя которого добавляем")
        bot.register_next_step_handler(msg, next_step, bot, 'first_user')
        return False
    if not check_enable_user(message.chat.id, message.from_user.username):
        bot.send_message(message.chat.id,
                         "Вам запрещен доступ к возможностям бота, напишите администратору для разблокировки")
        return False
    return True


def next_step(message: types.Message, bot: TeleBot, type_in: str, role: str = None, *args):
    
    if message.from_user.is_bot:
        bot.send_message(message.chat.id, "Доступ запрещен")
        return
    if not get_count_users() and type_in == 'first_user':
        add_tg_user(message.chat.id, message.from_user.username, 'admin', 1)
        bot.send_message(message.chat.id, "Администратор добавлен в систему", reply_markup=get_markup(role=get_role_user(message.chat.id)))
        return
    if not check_tg_usr(bot, message):
        return
    if role == 'admin' and type_in == 'add_vpn_login':
        for el in get_all_username():
            if el[0] == message.text:
                msg = bot.send_message(message.chat.id,
                                       'Такой пользователь уже существует. Введите имя нового пользователя',
                                       reply_markup=get_markup(lst=[back_button('admin')]))
                bot.register_next_step_handler(msg, next_step, bot, 'add_vpn_login', role)
                return
        msg = bot.send_message(message.chat.id, 'Введите пароль для пользователя', reply_markup=get_markup(lst=[back_button('admin')]))
        bot.register_next_step_handler(msg, next_step, bot, 'add_vpn_password', role, message.text)
        return
    if role == 'admin' and type_in == 'add_vpn_password':
        if message.text == 'Отмена':
            bot.send_message(message.chat.id, 'Доступные команды', reply_markup=get_markup(role=role))
        else:
            add_user(args[0], message.text, 'user')
            write_users_to_file([(el[0], el[1]) for el in get_all_username_vpn(enabled=1)])
            for el in get_all_username():
                if el[0] == args[0]:
                    bot.send_message(message.chat.id, 'Пользователь создан', reply_markup=get_markup(role=role))
                    break
            else:
                bot.send_message(message.chat.id, 'Пользователь не создан', reply_markup=get_markup(role=role))
        return
    if type_in == 'connect_vpn_login':
        if message.text == 'Отмена':
            bot.send_message(message.chat.id, 'Доступные команды', reply_markup=get_markup(role=role))
            return
        for el in get_my_account(message.chat.id):
            if el[0] == message.text:
                msg = bot.send_message(message.chat.id, 'Данный аккаунт уже привязан к вам',
                                       reply_markup=get_markup(lst=[back_button('start')]))
                bot.register_next_step_handler(msg, next_step, bot, 'connect_vpn_login', role)
                return
        msg = bot.send_message(message.chat.id, 'Введите пароль для пользователя', reply_markup=get_markup(lst=[back_button('start')]))
        bot.register_next_step_handler(msg, next_step, bot, 'connect_vpn_password', role, message.text)
        return
    if type_in == 'connect_vpn_password':
        if message.text == 'Отмена':
            bot.send_message(message.chat.id, 'Доступные команды', reply_markup=get_markup(role=role))
        else:
            for el in get_all_username():
                if el[0] == args[0] and el[1] == message.text:
                    if connect_tg_vpn(message.chat.id, args[0]) == 'edit':
                        bot.send_message(message.chat.id, 'Аккаунт привязан к вам', reply_markup=get_markup(role=role))
                    else:
                        bot.send_message(message.chat.id, 'Ошибка привязки аккаунта',
                                         reply_markup=get_markup(role=role))
                    return
        return
    

def check_enable_user(user_id, username):
    enabled = get_enable_user(user_id)
    if enabled is None:
        add_tg_user(user_id, username, 'user', 0)
        return False
    elif enabled == 1:
        return True
    return False


def get_markup(role: str = None, lst=None):
    row = []
    fn = lambda x: row.append(types.InlineKeyboardButton(x.caption, callback_data=x.key))
    if lst is not None:
        for el in lst:
            fn(el)
    elif role is not None:
        if role == 'admin':
            fn(admin_button)
        for el in user_buttons:
            fn(el)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(*row)
    return markup


def get_table_str(head: list, data: list):
    table = PrettyTable()
    table.field_names = head  # Установка заголовков столбцов
    for row in data:
        table.add_row(row)
    return f"<pre>{table}</pre>"



def check_button_call(bot: TeleBot, call, role: str):
    def admin_page(x): 
        try:
            bot.edit_message_text(
                x,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=get_markup(lst=[*admin_buttons, back_button('start')])
            )
        except Exception as e:
            pass
    def start_page(x):
        try:
            bot.edit_message_text(
                x,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=get_markup(role=get_role_user(call.from_user.id))
            )
        except Exception as e:
            pass
    
    def extract_text(s, matchs):
        match = re.search(f'(?:{matchs})(.*)', s)
        return match.group(1) if match else None
    
    if call.data == back_button('start').key:
        bot.edit_message_text(
            "Выберите действие",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=get_markup(role=get_role_user(call.from_user.id))
        )
    elif role == 'admin' and (call.data == admin_button.key or call.data == back_button('admin').key):
        admin_page("Выберите действие")
    elif role == 'admin' and call.data in (unlock_tg_button.key, lock_tg_button.key, unlock_vpn_button.key, lock_vpn_button.key):
        if call.data == unlock_tg_button.key:
            type_in = unlock_tg_button
            blocked = [el[1] for el in get_all_tg_username(enabled=0)]
            text = 'разблокировки'
        elif call.data == lock_tg_button.key:
            type_in = lock_tg_button
            blocked = [el[1] for el in get_all_tg_username(enabled=1)]
            text = 'блокировки'
        elif call.data == unlock_vpn_button.key:
            type_in = unlock_vpn_button
            blocked = [el[0] for el in get_all_username_vpn(0)]
            text = 'разблокировки'
        elif call.data == lock_vpn_button.key:
            type_in = lock_vpn_button
            blocked = [el[0] for el in get_all_username_vpn(1)]
            text = 'блокировки'
        
        lst_btn = [Button(f'{type_in.key}_{el}', el) for el in blocked]

        if not len(blocked):
            admin_page("Пользователей нет")
            return
        bot.edit_message_text(
            f'Выберите пользователя для {text}',
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=get_markup(lst=[*lst_btn, back_button('admin')])
        )
    elif role == 'admin' and (str(call.data).startswith(unlock_tg_button.key) or str(call.data).startswith(lock_tg_button.key)):
        type_in = str(call.data).startswith(unlock_tg_button.key)
        user = extract_text(call.data, f'{unlock_tg_button.key}_|{lock_tg_button.key}_')
        res = enable_user_tg(user, 1) if type_in else enable_user_tg(user, 0)
        if res == 'edit':
            msg = 'разблокирован' if type_in else 'заблокирован'
            admin_page(f"Пользователь {msg}")
            msg = "Вам дали доступ к боту" if type_in else "Вам ограничили доступ к боту"
            for usr in get_all_tg_username(user, 1):
                try:
                    bot.send_message(usr[0], msg, reply_markup=get_markup(role=usr[2]))
                except Exception as e:
                    pass
        else:
            msg = 'разблокировке' if type_in else 'блокировке'
            admin_page(f"Ошибка при {msg} пользователя")
    elif role == 'admin' and (str(call.data).startswith(unlock_vpn_button.key) or str(call.data).startswith(lock_vpn_button.key)):
        type_in = str(call.data).startswith(unlock_vpn_button.key)
        user = extract_text(call.data, f'{unlock_vpn_button.key}_|{lock_vpn_button.key}_')
        res = enable_user_vpn(user, 1) if type_in else enable_user_vpn(user, 0)
        if res == 'edit':
            write_users_to_file([(el[0], el[1]) for el in get_all_username_vpn(enabled=1)])
            msg = 'разблокирован' if type_in else 'заблокирован'
            admin_page(f"Пользователь {msg}")
            msg = "Вам дали доступ к боту" if type_in else "Вам ограничили доступ к боту"
            for usr in get_all_tg_username(user, 1):
                bot.send_message(usr[0], msg, reply_markup=get_markup(role=usr[2]))
        else:
            msg = 'разблокировке' if type_in else 'блокировке'
            admin_page(f"Ошибка при {msg} пользователя")
    elif role == 'admin' and call.data == delete_tg_button.key:
        lst_btn = [Button(f'{delete_tg_button.key}_{el[0]}', el[1]) for el in get_all_tg_username()]
        if not len(lst_btn):
            admin_page("Пользователей нет")
            return
        bot.edit_message_text(
            f'Выберите пользователя для удаления',
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=get_markup(lst=[*lst_btn, back_button('admin')])
        )
    elif role == 'admin' and str(call.data).startswith(delete_tg_button.key):
        user = extract_text(call.data, f'{delete_tg_button.key}_')
        res = delete_tg_user(user)
        if res == 'edit':
            admin_page(f"Пользователь удален")
        else:
            admin_page(f"Ошибка при удалении пользователя {res}")
    elif role == 'admin' and call.data == del_all_ses_button.key:
        if delete_session():
            admin_page('Все сессии удалены')
        else:
            admin_page('Ошибка удаления сессий')
    elif role == 'admin' and call.data == show_all_ses_button.key:
        data = get_all_processes()
        if not len(data):
            admin_page('Список сессий пуст')
            return
        table_str = get_table_str(['PID', 'Local IP', 'Name'], data)
        try:
            bot.edit_message_text(
                table_str,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=get_markup(lst=[show_all_ses_button, back_button('admin')])
            )
        except Exception as e:
            pass
    elif role == 'admin' and call.data == show_all_tg_user_button.key:
        data = get_all_tg_username()
        if not len(data):
            admin_page('Список пользователей пуст')
            return
        table_str = get_table_str(['USR_ID', 'NAME', 'ROLE', 'ENABLED'], data)
        bot.edit_message_text(
            table_str,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_markup(lst=[back_button('admin')])
        )
    elif role == 'admin' and call.data == show_all_vpn_user_button.key:
        data = get_all_username_vpn()
        if not len(data):
            admin_page('Список пользователей пуст')
            return
        table_str = get_table_str(['USR', 'PASSWORD', 'STATUS'], data)
        bot.edit_message_text(
            table_str,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_markup(lst=[back_button('admin')])
        )
    elif role == 'admin' and call.data == add_user_vpn_button.key:
        msg = bot.send_message(call.message.chat.id, 'Введите имя нового пользователя', reply_markup=get_markup(lst=[back_button('admin')]))
        bot.register_next_step_handler(msg, next_step, bot, 'add_vpn_login', role)
    elif call.data == connect_acc_button.key:
        msg = bot.send_message(call.message.chat.id, 'Введите логин вашего пользователя', reply_markup=get_markup(lst=[back_button('start')]))
        bot.register_next_step_handler(msg, next_step, bot, 'connect_vpn_login', role)
    elif call.data == show_my_acc_button.key:
        data = get_my_account(call.from_user.id)
        if not len(data):
            start_page('У вас нет аккаунтов')
            return
        table_str = get_table_str(['USR', 'PASSWORD'], data)
        bot.edit_message_text(
            table_str,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_markup(lst=[back_button('start')])
        )
    elif call.data == del_my_ses_button.key:
        data = get_my_account(call.from_user.id)
        if not len(data):
            start_page('У вас нет аккаунтов')
            return
        btn = [Button(f'{del_my_ses_button.key}_{el[0]}', el[0]) for el in data]
        btn.append(all_button)
        btn.append(back_button('start'))
        bot.edit_message_text(
            'Выберете аккаунт для которого необходимо сбросить сессии',
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=get_markup(lst=btn)
        )
    elif (str(call.data).startswith(del_my_ses_button.key) or call.data == all_button.key):
        user = extract_text(call.data, f'{del_my_ses_button.key}_')
        text = []
        for el in get_my_account(call.from_user.id):
            if call.data == all_button.key or (not user is None and el[0] == user):
                if delete_session(el[0]):
                    text.append(f'Все сессии {el[0]} удалены')
                else:
                    text.append(f'Ошибка удаления {el[0]} сессий')
                if not user is None and el[0] == user:
                    break
        else:
            if call.data == all_button.key:
                text.append('Все привязанные сессии удалены')
            else:
                text.append(f'Пользователя {user} нет в списке привязанных')
        start_page('\n'.join(text))
    elif call.data == unconnect_acc_button.key:
        data = get_my_account(call.from_user.id)
        if not len(data):
            start_page('У вас нет аккаунтов')
            return
        btn = [Button(f'{unconnect_acc_button.key}_{el[0]}', el[0]) for el in data]
        btn.append(back_button('start'))
        bot.edit_message_text(
            'Выберете аккаунт для отвязки',
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=get_markup(lst=btn)
        )
    elif str(call.data).startswith(unconnect_acc_button.key):
        user = extract_text(call.data, f'{unconnect_acc_button.key}_')
        accounts = get_my_account(call.from_user.id)
        if not len(accounts):
            start_page("Нечего отвязывать")
            return
        for el in accounts:
            if el[0] == user:
                if unconnect_user(call.from_user.id, el[0]) == 'edit':
                    start_page("Аккаунт отвязан")
                else:
                    start_page("Ошибка отвязки аккаунта")
                break
        else:
            start_page("Такого аккаунта нет в привязанных")
    else:
        bot.send_message(call.message.chat.idcall.message.chat.id, 'Иди подальше', reply_markup=get_markup(role=role))