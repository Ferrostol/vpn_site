Установка на сервере Debian

Устанавливаем программы:

	apt install git wget
	apt-get install -y zlib1g-dev libbz2-dev libreadline-dev llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev liblzma-dev python3-dev python3-lxml libxslt-dev libffi-dev libssl-dev gnumeric libsqlite3-dev libpq-dev libxml2-dev libxslt1-dev libjpeg-dev libfreetype6-dev libcurl4-openssl-dev

Установка VPN:

	wget https://get.vpnsetup.net -O vpn.sh
	sudo VPN_IPSEC_PSK='<PSK_KEY>' \
	VPN_USER='<USERNAME_LOGIN>' \
	VPN_PASSWORD='<USERNAME_PASSWORD>' \
	VPN_SKIP_IKEV2=yes \
	sh vpn.sh


Настраиваем VPN для работы с ботом:

	vim /etc/ppp/options.xl2tpd

Дописываем строки:

	logfile /etc/ppp/log.log
	debug
	idle 0



Если нужна настройка для ограничения 1 пользователь = 1 сессия, то настраиваем далее, если нет, то переходим к "Перезагружаем службы":

	cp server/peer-lock.sh /etc/ppp
	mkdir /var/locks
	chmod 777 /var/locks
	vim /etc/ppp/ip-up

Добавляем в середину строки:

	if [ -x /etc/ppp/peer-lock.sh ]; then
		/etc/ppp/peer-lock.sh
		if [ $? -ne 0 ]; then
			kill $PPPD_PID
			exit 1
		fi
	fi

Выполняем команду:

	echo "rm -f /var/locks/$PEERNAME.lock" >> /etc/ppp/ip-down


Перезагружаем службы:

	systemctl restart ipsec.service
	systemctl restart xl2tpd.service


Устанавливаем Python:
 
	wget https://www.python.org/ftp/python/3.12.2/Python-3.12.2.tgz ; \
	tar xvf Python-3.12.* ; \
	cd Python-3.12.2 ; \
	mkdir ~/.python ; \
	./configure --enable-optimizations --prefix=/root/.python ; \
	make -j8 ; \
	make altinstall

Обновляем pip

	~/.python/bin/python3.12 -m pip install -U pip
	export PATH=~/.python/bin:$PATH

Скачиваем и запускаем бота

	git clone https://github.com/Ferrostol/vpn_site.git
	cd vpn_site
	git switch tg_bot_editable
	python3.12 -m venv venv
	. ./venv/bin/activate
	pip3.12 install -r requirements.txt
	cp server/vpn_bot.service /etc/systemd/system
	systemctl daemon-reload
	echo "token=YOUR_TOKEN" > src/.env
	systemctl enable vpn_bot.service


После этого пишем боту /start и регистрируемся первыми в качестве администратора
