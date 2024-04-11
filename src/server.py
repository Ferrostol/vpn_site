import re
from config import log_file, output_file
import subprocess
import os


ip_pattern = r'<addr\s+(\d+\.\d+\.\d+\.\d+)>'
ip_ps_pattern = r'\d+\.\d+\.\d+\.\d+\:(\d+\.\d+\.\d+\.\d+)'


def get_all_processes():
    try:
        # Выполнение команды ps с grep
        result = subprocess.run('/usr/bin/ps aux', shell=True, capture_output=True, text=True)
        # Поиск строк, содержащих xl2tpd и IP-адрес
        processes = []
        for line in result.stdout.split('\n'):
            if 'pppd plugin' in line:
                ip_ps = re.search(ip_ps_pattern, line).group(1)
                processes.append(
                    (
                        line.split()[1],
                        ip_ps,
                        get_last_name_for_ip(ip_ps)
                    )
                )
        if not len(processes):
            delete_file_logs()
        return processes
    except Exception as e:
        return str(e)
    

def get_last_name_for_ip(ip_address):
    try:
        # Читаем содержимое файла
        with open(log_file, 'r') as file:
            lines = file.readlines()
        
        # Ищем последнее вхождение подстроки
        last_match_index = -1
        ln_line = len(lines)
        for i in range(ln_line - 1, -1, -1):
            if 'ConfNak' in lines[i] and ip_address in lines[i]:
                last_match_index = i
                break
        
        if last_match_index == -1:
            return None
        
        # Ищем строку с "ConfNak" после последнего вхождения подстроки
        for i in range(last_match_index - 1, -1, -1):
            if 'CHAP Response' in lines[i]:
                return re.search(r'name\s+=\s+\"(\w+)\"', lines[i]).group(1)
        return None

    except FileNotFoundError:
        return None
    

def delete_session(username):
    try:
        # Выполнение команды ps с grep
        result = get_all_processes()
        # Поиск строк, содержащих xl2tpd и IP-адрес
        processes = [info for info in result if info[2] == username or username is None]
        for proc in processes:
            subprocess.run(f'/usr/bin/kill {proc[0]}', shell=True, capture_output=True, text=True)
        if username is None:
            delete_file_logs()
        return True
    except Exception:
        return False


def delete_file_logs():
    if os.path.exists(log_file):
        os.remove(log_file)


def write_users_to_file(users):
    try:
        # Открываем файл для записи
        with open(output_file, 'w') as file:
            # Записываем данные пользователей в файл
            for username, password in users:
                file.write(f'"{username}" l2tpd "{password}" *\n')
        print("Данные успешно записаны в файл:", output_file)
        
        subprocess.run('systemctl restart xl2tpd.service', shell=True, capture_output=True, text=True)
        return None
    except Exception as e:
        return e
