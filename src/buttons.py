class Button:
    def __init__(self, key: str, caption: str):
        self.key = key
        self.caption = caption


cancel_button = Button('cancel', 'Отмена')
back_button = lambda x: Button(f'back_{x}', 'Назад')
admin_button = Button('admin', 'Админ')

unlock_tg_button = Button('unlock_tg', 'Дать доступ пользователю TG')
delete_tg_button = Button('delete_tg', 'Удалить пользователя TG')
lock_tg_button = Button('lock_tg', 'Заблокировать пользователя TG')
add_user_vpn_button = Button('add_user_vpn', 'Добавить пользователя VPN')
unlock_vpn_button = Button('unlock_vpn', 'Разблокировать пользователя VPN')
lock_vpn_button = Button('lock_vpn', 'Заблокировать пользователя VPN')
del_all_ses_button = Button('del_all_ses', 'Удалить все сессии')
show_all_ses_button = Button('show_all_ses', 'Посмотреть текущие сессии')
show_all_tg_user_button = Button('show_all_tg_user', 'Посмотреть пользователей TG')
show_all_vpn_user_button = Button('show_all_vpn_user', 'Посмотреть пользователей VPN')

show_my_acc_button = Button('show_my_acc', 'Посмотреть свои аккаунты')
connect_acc_button = Button('connect_acc', 'Привязать аккаунт')
unconnect_acc_button = Button('unconnect_acc', 'Отвязать аккаунт')
del_my_ses_button = Button('del_my_ses', 'Удалить свои сессии')
all_button = Button('all_delete', 'Все')

admin_buttons = [
    unlock_tg_button,
    lock_tg_button,
    delete_tg_button,
    add_user_vpn_button,
    unlock_vpn_button,
    lock_vpn_button,
    del_all_ses_button,
    show_all_ses_button,
    show_all_tg_user_button,
    show_all_vpn_user_button
]
user_buttons = [
    show_my_acc_button,
    connect_acc_button,
    unconnect_acc_button,
    del_my_ses_button
]