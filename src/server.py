import re
import subprocess
import os
import shutil

import config
from config import set_key_env


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
        with open(config.log_file, 'r') as file:
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


def delete_session(username=None):
    try:
        # Выполнение команды ps с grep
        result = get_all_processes()
        # Поиск строк, содержащих xl2tpd и IP-адрес
        processes = [info for info in result if info[2] == username or username is None]
        for proc in processes:
            subprocess.run(f'/usr/bin/kill {proc[0]}', shell=True, capture_output=True, text=True)
        if config.multi_connect:
            if username is None:
                subprocess.run(f'/usr/bin/rm -f /var/locks/*.lock', shell=True, capture_output=True, text=True)
                delete_file_logs()
            else:
                subprocess.run(f'/usr/bin/rm -f /var/locks/{username}.lock', shell=True, capture_output=True, text=True)
        elif username is None:
            delete_file_logs()
        return True
    except Exception:
        return False


def delete_file_logs():
    if os.path.exists(config.log_file):
        os.remove(config.log_file)


def reboot_vpn():
    subprocess.run('/usr/bin/systemctl restart xl2tpd.service', shell=True, capture_output=True, text=True)


def write_users_to_file(users):
    try:
        # Открываем файл для записи
        with open(config.output_file, 'w') as file:
            # Записываем данные пользователей в файл
            for username, password in users:
                file.write(f'"{username}" l2tpd "{password}" *\n')
        reboot_vpn()
        return None
    except Exception as e:
        return e


def edit_multi_connect(enabled: bool):
    config.load_env()
    env = enabled == config.multi_connect

    def found(file, target):
        found = False
        with open(file, "r", encoding="utf-8") as f:
            found = any(target in line for line in f)
        return found

    def filtered_file(file):
        start_marker = "#START_MULTI_CONNECT"
        end_marker = "#END_MULTI_CONNECT"

        with open(file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        inside_block = False
        filtered_lines = []

        for line in lines:
            if start_marker in line:
                inside_block = True
                continue  # пропустить строку с маркером начала
            if end_marker in line:
                inside_block = False
                continue  # пропустить строку с маркером конца
            if not inside_block:
                filtered_lines.append(line)

        with open(file, "w", encoding="utf-8") as f:
            f.writelines(filtered_lines)

    vpn_up_file: bool = found("/etc/ppp/ip-up", 'peer-lock.sh') == enabled
    vpn_peer_file: bool = os.path.isfile('/etc/ppp/peer-lock.sh') == enabled
    vpn_locks_path: bool = os.path.exists('/var/locks') == enabled
    vpn_down_file: bool = found("/etc/ppp/ip-down", '/var/locks/') == enabled

    count_need_edit = [vpn_up_file, vpn_peer_file, vpn_locks_path, vpn_down_file].count(False)
    vpn_all: bool = count_need_edit == 0

    if enabled:
        if not env:
            set_key_env(config.multi_connect_key, 'Y')
        if not vpn_up_file:
            with open('/etc/ppp/ip-up', 'a') as file:
                file.write('''
#START_MULTI_CONNECT
if [ -x /etc/ppp/peer-lock.sh ]; then
  /etc/ppp/peer-lock.sh
  if [ $? -ne 0 ]; then
    kill $PPPD_PID
    exit 1
  fi
fi
#END_MULTI_CONNECT''')
        if not vpn_peer_file:
            shutil.copy(
                '../server/peer-lock.sh',
                '/etc/ppp/peer-lock.sh'
            )
        if not vpn_locks_path:
            os.mkdir("/var/locks")
            os.chmod('/var/locks', 0o777)
        if not vpn_down_file:
            with open('/etc/ppp/ip-down', 'a') as file:
                file.write("\n#START_MULTI_CONNECT\nrm -f /var/locks/$PEERNAME.lock\n#END_MULTI_CONNECT")
    else:
        if not env:
            set_key_env(config.multi_connect_key, 'N')
        if not vpn_up_file:
            filtered_file('/etc/ppp/ip-up')
        if not vpn_peer_file:
            os.remove('/etc/ppp/peer-lock.sh')
        if not vpn_locks_path:
            shutil.rmtree('/var/locks')
        if not vpn_down_file:
            filtered_file('/etc/ppp/ip-down')

    if count_need_edit > 0:
        reboot_vpn()
    if env and vpn_all:
        return 'Уже включен' if enabled else 'Уже выключен'
    elif not env and vpn_all:
        return 'Уже включен, просто был не изменен конфиг' if enabled else 'Уже выключен, просто был не изменен конфиг'


def reboot_server():
    subprocess.run('/usr/sbin/reboot', shell=True, capture_output=True, text=True)


def update_bot():
    subprocess.run('/usr/bin/git fetch && /usr/bin/git pull', shell=True, capture_output=True, text=True)
    restart_bot()

def restart_bot():
    subprocess.run('/usr/bin/systemctl restart vpn_bot.service', shell=True, capture_output=True, text=True)