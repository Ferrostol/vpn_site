import re
from config import log_file, output_file
import subprocess

ip_pattern = r'<addr\s+(\d+\.\d+\.\d+\.\d+)>'

def get_ip_user(username):
    try:
        # Читаем содержимое файла
        with open(log_file, 'r') as file:
            lines = file.readlines()
        
        # Ищем последнее вхождение подстроки
        last_match_index = -1
        for i in range(len(lines)):
            if username in lines[i]:
                last_match_index = i
        
        if last_match_index == -1:
            return None
        
        # Ищем строку с "ConfNak" после последнего вхождения подстроки
        for i in range(last_match_index, len(lines)):
            if "ConfNak" in lines[i]:
                ip_address_match = re.search(ip_pattern, lines[i])
                return ip_address_match.group(1)
        return None

    except FileNotFoundError:
        return None
    
def get_processes(ip_address):
    try:
        # Выполнение команды ps с grep
        result = subprocess.run('/usr/bin/ps aux', shell=True, capture_output=True, text=True)
        # Поиск строк, содержащих xl2tpd и IP-адрес
        processes = [line for line in result.stdout.split('\n') if 'xl2tpd' in line and ip_address in line]
        return processes
    except Exception as e:
        return str(e)

def delete_session(username):
    try:
        ip_address = get_ip_user(username)
        processes = get_processes(ip_address)
        for proc in processes:
            pid = proc.split()[1]
            subprocess.run(f'/usr/bin/kill {pid}', shell=True, capture_output=True, text=True)
        return True
    except Exception:
        return False


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
