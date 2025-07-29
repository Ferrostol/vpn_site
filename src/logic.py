from telebot import TeleBot, types, apihelper

import database
from buttons import Button, Result, start_buttons


def start_program():
    database.create_table()
    database.create_table_bot()


def check_enable_user(user_id, username):
    enabled = database.get_enable_user(user_id)
    if enabled is None:
        database.add_tg_user(user_id, username, 'user', 0)
        return False
    elif enabled == 1:
        return True
    return False


def check_tg_usr(bot: TeleBot, message: types.Message):
    if not database.get_count_users():
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


def next_step(message: types.Message, bot: TeleBot, type_in: str, next=None, *args):
    if message.from_user.is_bot:
        bot.send_message(message.chat.id, "Доступ запрещен")
        return
    if not database.get_count_users() and type_in == 'first_user':
        database.add_tg_user(message.chat.id, message.from_user.username, 'admin', 1)
        bot.send_message(message.chat.id, "Администратор добавлен в систему",
                         reply_markup=start_buttons.get_markup(role=database.get_role_user(message.chat.id)))
        return
    if not check_tg_usr(bot, message):
        return
    role = database.get_role_user(message.chat.id)
    result = next(message.text, role, *args)
    msg = bot.send_message(
        message.chat.id,
        result.text,
        reply_markup=result.btn.get_markup(role=role),
        parse_mode=result.btn.parse_mode
    )
    if result.next_step is not None:
        bot.register_next_step_handler(msg, next_step, bot, None, result.next_step)


def check_button_call(bot: TeleBot, call, role: str):
    chat_id = call.message.chat.id
    bot.clear_step_handler(call.message)
    btn = Button.get_buttons(start_buttons, role, call.data, chat_id)
    result: Result = btn.analize(btn, chat_id)
    if result is not None:
        btn = result.btn
        text = result.text
        next = result.next_step
    elif btn.is_work:
        result: Result = btn.work_def(btn, chat_id, role)
        btn: Button = result.btn
        text = result.text
        next = result.next_step
    else:
        text = btn.text
        next = None
    try:
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=btn.get_markup(role=role, chat_id=chat_id),
            parse_mode=btn.parse_mode
        )
        if next is not None:
            bot.register_next_step_handler(call.message, next_step, bot, None, next)
    except apihelper.ApiTelegramException as e:
        if "message is not modified" in e.description:
            pass
        else:
            print(e)
    except Exception as e:
        print(e)