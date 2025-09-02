#!/bin/bash

set -euo pipefail

CURRENT_DIR="$(pwd)"

### === Парсим аргументы в формате VAR=VALUE === ###
for ARG in "$@"; do
  case $ARG in
    PSK_KEY=*) PSK_KEY="${ARG#*=}" ;;
    USERNAME_LOGIN=*) USERNAME_LOGIN="${ARG#*=}" ;;
    USERNAME_PASSWORD=*) USERNAME_PASSWORD="${ARG#*=}" ;;
    BOT_TOKEN=*) BOT_TOKEN="${ARG#*=}" ;;
    MULTI_CONNECT=*) MULTI_CONNECT="${ARG#*=}" ;;
    *)
      echo "Неизвестный аргумент: $ARG"
      exit 1
      ;;
  esac
done

### === Функция безопасного запроса переменной === ###
prompt_until_nonempty() {
  local var_name="$1"
  local prompt_text="$2"
  local input=""

  while [ -z "${!var_name:-}" ]; do
    read -rp "$prompt_text: " input
    if [ -n "$input" ]; then
      export "$var_name"="$input"
    else
      echo "Значение не может быть пустым. Повторите ввод."
    fi
  done
}

### === Запрос переменных, если они не переданы === ###
prompt_until_nonempty PSK_KEY "Введите PSK_KEY (Pre-Shared Key)"
prompt_until_nonempty USERNAME_LOGIN "Введите имя пользователя VPN (USERNAME_LOGIN)"
prompt_until_nonempty USERNAME_PASSWORD "Введите пароль VPN (USERNAME_PASSWORD)"
prompt_until_nonempty BOT_TOKEN "Введите Telegram bot token (BOT_TOKEN)"

# MULTI_CONNECT: Y/N
while [[ -z "${MULTI_CONNECT:-}" || ! "$MULTI_CONNECT" =~ ^[YyNn]$ ]]; do
  read -rp "Разрешить одновременные подключения (Y/N)? " MULTI_CONNECT
  export MULTI_CONNECT
done

### === Установка зависимостей === ###
apt update
apt install -y git wget
apt-get install -y \
  zlib1g-dev libbz2-dev libreadline-dev llvm libncurses5-dev libncursesw5-dev \
  xz-utils tk-dev liblzma-dev python3-dev python3-lxml libxslt-dev libffi-dev \
  libssl-dev gnumeric libsqlite3-dev libpq-dev libxml2-dev libxslt1-dev \
  libjpeg-dev libfreetype6-dev libcurl4-openssl-dev

### === Установка VPN === ###
wget https://get.vpnsetup.net -O vpn.sh
chmod +x vpn.sh
VPN_IPSEC_PSK="$PSK_KEY" \
VPN_USER="$USERNAME_LOGIN" \
VPN_PASSWORD="$USERNAME_PASSWORD" \
VPN_SKIP_IKEV2=yes \
sh vpn.sh

### === Настройка VPN для бота === ###
cat <<EOF >> /etc/ppp/options.xl2tpd
logfile /etc/ppp/log.log
debug
idle 0
EOF


### === Установка Python 3.12.2 === ###
cd /tmp
wget https://www.python.org/ftp/python/3.12.2/Python-3.12.2.tgz
tar xvf Python-3.12.2.tgz
cd Python-3.12.2
mkdir -p ~/.python
./configure --enable-optimizations --prefix=/root/.python
make -j"$(nproc)"
make altinstall

/root/.python/bin/python3.12 -m pip install -U pip
export PATH=/root/.python/bin:$PATH

### === Установка бота === ###
cd "$CURRENT_DIR"
git clone https://github.com/Ferrostol/vpn_site.git
cd vpn_site
git switch tg_bot_editable
/root/.python/bin/python3.12 -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt



### === Настройка ограничения 1 пользователь = 1 сессия === ###
if [[ "$MULTI_CONNECT" =~ ^[Yy]$ ]]; then
  if [ -f server/peer-lock.sh ]; then
    cp server/peer-lock.sh /etc/ppp
    mkdir -p /var/locks
    chmod 777 /var/locks

    if ! grep -q "peer-lock.sh" /etc/ppp/ip-up; then
      cat <<'EOF' >> /etc/ppp/ip-up

if [ -x /etc/ppp/peer-lock.sh ]; then
  /etc/ppp/peer-lock.sh
  if [ $? -ne 0 ]; then
    kill $PPPD_PID
    exit 1
  fi
fi

EOF
    fi

    echo 'rm -f /var/locks/$PEERNAME.lock' >> /etc/ppp/ip-down
  fi
fi

### === Перезапуск служб === ###
systemctl restart ipsec.service
systemctl restart xl2tpd.service

### === Запуск бота === ###
cp server/vpn_bot.service /etc/systemd/system
sed -i "s|/root/|$CURRENT_DIR/|g" /etc/systemd/system/vpn_bot.service
systemctl daemon-reload
echo "TOKEN=$BOT_TOKEN" > src/.env
echo "MULTI_CONNECT=$MULTI_CONNECT" >> src/.env
systemctl enable vpn_bot.service