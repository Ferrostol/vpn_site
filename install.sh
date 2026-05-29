#!/bin/bash

set -euo pipefail

CURRENT_DIR="$(pwd)"

prompt_until_nonempty() {
  local var_name="$1"
  local prompt_text="$2"
  local default_v="$3"
  local input=""

  while [ -z "${!var_name:-}" ]; do
    read -rp "$prompt_text [$default_v]: " input
    if [ -n "$input" ]; then
      export "$var_name"="$input"
    else
      export "$var_name"="$default_v"
    fi
  done
}

prompt_until_nonempty_yn() {
  local var_name="$1"
  local prompt_text="$2"
  local default_v="$3"
  local input=""

  while [[ -z "${!var_name:-}" || ! "${!var_name:-}" =~ ^[YyNn]$ ]]; do
    read -rp "$prompt_text (Y/N)[$default_v]? " input
    if [ -n "$input" ]; then
      export "$var_name"="$input"
    else
      export "$var_name"="$default_v"
    fi
  done
}

configure_vars() {
  prompt_until_nonempty PSK_KEY "Введите PSK_KEY (Pre-Shared Key)" "psk"
  prompt_until_nonempty USERNAME_LOGIN "Введите имя пользователя VPN (USERNAME_LOGIN)" "login"
  prompt_until_nonempty USERNAME_PASSWORD "Введите пароль VPN (USERNAME_PASSWORD)" "password"

  prompt_until_nonempty VPN_L2TP_NET "Укажите подсеть (VPN_L2TP_NET)" "192.168.42.0/16"
  prompt_until_nonempty VPN_L2TP_LOCAL "Укажите gateway (VPN_L2TP_LOCAL)" "192.168.42.1"
  prompt_until_nonempty VPN_L2TP_POOL "Укажите пул адресов (VPN_L2TP_POOL)" "192.168.42.10-192.168.42.250"

  prompt_until_nonempty BOT_TOKEN "Введите Telegram bot token (BOT_TOKEN)" "NONE"
  prompt_until_nonempty_yn MULTI_CONNECT "Разрешить одновременные подключения" "Y"
}

install_pkg() {
  apt update
  apt install -y git wget
  apt-get install -y \
    zlib1g-dev libbz2-dev libreadline-dev llvm libncurses5-dev libncursesw5-dev \
    xz-utils tk-dev liblzma-dev python3-dev python3-lxml libxslt-dev libffi-dev \
    libssl-dev gnumeric libsqlite3-dev libpq-dev libxml2-dev libxslt1-dev \
    libjpeg-dev libfreetype6-dev libcurl4-openssl-dev
}

install_vpn() {
  wget https://get.vpnsetup.net -O vpn.sh
  chmod +x vpn.sh
  VPN_IPSEC_PSK="$PSK_KEY" \
  VPN_USER="$USERNAME_LOGIN" \
  VPN_PASSWORD="$USERNAME_PASSWORD" \
  VPN_L2TP_NET="$VPN_L2TP_NET" \
  VPN_L2TP_LOCAL="$VPN_L2TP_LOCAL" \
  VPN_L2TP_POOL="$VPN_L2TP_POOL" \
  sh vpn.sh

  cat << 'EOF' >> /etc/ppp/options.xl2tpd
    logfile /etc/ppp/log.log
    debug
    idle 0
EOF
}

install_python() {
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
}

install_bot() {
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

  cp server/vpn_bot.service /etc/systemd/system
  sed -i "s|/root/|$CURRENT_DIR/|g" /etc/systemd/system/vpn_bot.service
  echo "TOKEN=$BOT_TOKEN" > src/.env
  echo "MULTI_CONNECT=$MULTI_CONNECT" >> src/.env
}

start_bot() {
  systemctl daemon-reload
  systemctl restart ipsec.service
  systemctl restart xl2tpd.service
  systemctl enable vpn_bot.service
}

vpnsetup() {
  configure_vars
  install_pkg
  install_vpn
  install_python
  install_bot
  start_bot
}

## Defer setup until we have the complete script
vpnsetup "$@"