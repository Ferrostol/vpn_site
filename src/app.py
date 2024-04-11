from flask import Flask, render_template, request, redirect, url_for, make_response
from database import create_table, get_role_user
from logic import get_start_page, check_role, delete_my_session, add_new_user, configure_file_users, get_count_users, check_all_processes

# Создаем экземпляр сайта
app = Flask(__name__)

# Создание таблицы пользователей перед запуском сервера
create_table()

exists_user = get_count_users() > 0

@app.route('/', methods=['GET', 'POST'])
def login():
    global exists_user
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role_user = get_role_user(username, password)
        if role_user and role_user in ('admin', 'user'):
            response = make_response(redirect(url_for(role_user)))
            response.set_cookie('username', username)
            return response
        return get_start_page(error=True)
    username = request.cookies.get('username')
    if username:
        role = get_role_user(username)
        if role in ('admin', 'user'):
            return redirect(url_for(role))
    if not exists_user:
        return make_response(redirect(url_for('admin')))
    return get_start_page()


@app.route('/user', methods=['GET', 'POST'])
def user():
    username = request.cookies.get('username')
    match check_role(username, 'user'):
        case True:
            if request.method == 'POST':
                match list(request.form)[-1]:
                    case 'delete_session':
                        return delete_my_session(username, 'user')
                    case 'exit':
                        return get_start_page(redirected=True)
            error = request.cookies.get('error')
            response = make_response(render_template('user.html', username=username, error=error))
            if error:
                response.delete_cookie('error')
            return response
        case False:
            return redirect(url_for('admin'))
    return get_start_page(redirected=True)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    global exists_user
    username = request.cookies.get('username')
    match (check_role(username, 'admin'), exists_user):
        case (role, False):
            if request.method == 'POST' and list(request.form)[-1] == 'add_user':
                add_new_user(request.form)
                exists_user = True
                return redirect(url_for('admin'))
            response = make_response(render_template('admin.html'))
            return response
        case (True, exists):
            if request.method == 'POST':
                match list(request.form)[-1]:
                    case 'add_user':
                        add_new_user(request.form)
                        exists_user = True
                        return redirect(url_for('admin'))
                    case 'write_users_to_file':
                        return configure_file_users()
                    case 'delete_all_session':
                        return delete_my_session(None, 'admin')
                    case 'delete_session':
                        return delete_my_session(username, 'admin')
                    case 'exit':
                        return get_start_page(redirected=True)
            error = request.cookies.get('error')
            all_session = check_all_processes()
            response = make_response(render_template('admin.html', error=error, all_session=all_session))
            if error:
                response.delete_cookie('error')
            return response
        case (False, exists):
            return redirect(url_for('user'))
    return get_start_page(redirected=True)


if __name__ == '__main__':
    app.run(debug=True)
