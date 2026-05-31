import re
import subprocess
import os
import shutil

import config
from config import set_key_env


def get_all_processes():
    try:
        result = subprocess.run(f'/usr/bin/tdbdump {config.tdb_file_ppp}', shell=True, capture_output=True, text=True)
        processes = []
        for line in result.stdout.split('\n'):
            if 'PEERNAME' in line:
                payload = re.search(r'"(.*)"', line).group(1)
                payload = payload.replace("\\00", "").replace("\x00", "")
                data = dict(item.split("=", 1) for item in payload.split(";") if "=" in item)
                processes.append(
                    (
                        data.get("PPPD_PID"),
                        data.get("IPREMOTE"),
                        data.get("PEERNAME")
                    )
                )
        return processes
    except Exception as e:
        return str(e)


def delete_session(username=None):
    try:
        # Выполнение команды ps с grep
        result = get_all_processes()
        # Поиск строк, содержащих xl2tpd и IP-адрес
        processes = [info for info in result if info[2] == username or username is None]
        for proc in processes:
            subprocess.run(f'/usr/bin/kill {proc[0]}', shell=True, capture_output=True, text=True)
        if not config.multi_connect:
            if username is None:
                subprocess.run(f'/usr/bin/rm -f /var/locks/*.lock', shell=True, capture_output=True, text=True)
            else:
                subprocess.run(f'/usr/bin/rm -f /var/locks/{username}.lock', shell=True, capture_output=True, text=True)
        return True
    except Exception:
        return False


def reboot_vpn():
    subprocess.run('/usr/bin/systemctl restart xl2tpd.service', shell=True, capture_output=True, text=True)


def write_users_to_file(users):
    try:
        # Открываем файл для записи
        with open(config.output_file, 'w') as file:
            # Записываем данные пользователей в файл
            for username, password in users:
                file.write(f'"{username}" l2tpd "{password}" *\n')
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

    count_need_edit = [vpn_up_file, vpn_peer_file, vpn_locks_path, vpn_down_file].count(True)
    vpn_all: bool = count_need_edit == 0

    if not enabled:
        if not env:
            set_key_env(config.multi_connect_key, 'N')
        if vpn_up_file:
            with open("/etc/ppp/ip-up", "ab") as out, open("../config/vpn_server/ip-up", "rb") as inp:
                shutil.copyfileobj(inp, out)
        if vpn_peer_file:
            shutil.copy(
                '../config/vpn_server/peer-lock.sh',
                '/etc/ppp/peer-lock.sh'
            )
        if vpn_locks_path:
            os.mkdir("/var/locks")
            os.chmod('/var/locks', 0o777)
        if vpn_down_file:
            with open("/etc/ppp/ip-down", "ab") as out, open("../config/vpn_server/ip-down", "rb") as inp:
                shutil.copyfileobj(inp, out)
    else:
        if not env:
            set_key_env(config.multi_connect_key, 'Y')
        if vpn_up_file:
            filtered_file('/etc/ppp/ip-up')
        if vpn_peer_file:
            os.remove('/etc/ppp/peer-lock.sh')
        if vpn_locks_path:
            shutil.rmtree('/var/locks')
        if vpn_down_file:
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

def get_ipsec_key():
    with open(config.ipsec_file, 'r') as file:
        text = file.read()
    matches = re.findall(r':\s*PSK\s+(?:"([^"]+)"|([^\s"\n]+))', text, flags=re.IGNORECASE)
    keys = [m[0] or m[1] for m in matches]
    for i, key in enumerate(keys, 1):
        return key
    return None