Установка на сервере Debian

	apt install git wget
	apt-get install -y zlib1g-dev libbz2-dev libreadline-dev llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev liblzma-dev python3-dev python3-lxml libxslt-dev libffi-dev libssl-dev gnumeric libsqlite3-dev libpq-dev libxml2-dev libxslt1-dev libjpeg-dev libfreetype6-dev libcurl4-openssl-dev

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
	git switch telegram_bot
	python3.12 -m venv venv
	. ./venv/bin/activate
	pip3.12 install -r requirements.txt
	cp vpn_bot.service /etc/systemd/system
	systemctl daemon-reload
	systemctl enable vpn_bot.service
