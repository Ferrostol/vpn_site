from database import get_role_user, add_user, get_count_users
from flask import render_template, redirect, make_response, url_for
from server import delete_session, write_users_to_file


def check_count_user():
    return get_count_users()

def get_start_page(redirected = False, error = False):
    if redirected:
        response = make_response(redirect('/'))
    else:
        response = make_response(render_template('login.html', error=error))
    response.delete_cookie('username')
    return response

def add_new_user(form):
    username = form['username']
    password = form['password']
    role = form['role']
    add_user(username, password, role)

def check_role(username, role = None):
    if not username:
        return None
    real_role = get_role_user(username)
    if real_role and real_role == role:
        return True
    return False


def delete_my_session(username, to):
    error = not delete_session(username)
    response = make_response(redirect(url_for(to)))
    response.set_cookie('error', f'session_{str(error)}')
    return response


def configure_file_users():
    error = write_users_to_file()
    response = make_response(redirect(url_for('admin')))
    response.set_cookie('error', f'password_{str(error)}')
    return response