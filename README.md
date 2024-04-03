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

Скачиваем и запускаем сайт

	git clone https://github.com/Ferrostol/vpn_site.git
	cd vpn_site
	python3.12 -m venv venv
	. ./venv/bin/activate
	pip3.12 install -r requirements.txt
	pip3.12 install gunicorn
	cp vpn_site.service /etc/systemd/system
	systemctl daemon-reload
	systemctl enable vpn_site.service




Работа с проектом в PyCharm

	1. Открываем PyCharm
	2. Нажимаем "Get from VCS"
	3. Указываем ссылку на git и папку в которой будет храниться данные
	4. Клонируем репозиторий
	5. В отрывшемся проекте в правом нижнем углу надо будет создать виртуальное окружение. Для этого:
		1. Нажимаем "Add New Interpreter" -> "Add Local Interpreter"
		2. Устанавливаем параметры: Enviroment = New; Location = путь до проекта + папка venv; Base interpreter = указываем установленный на компе python
		3. Далее после создание папки venv открываем файл requirements.txt и нажимаем кнопку "Install requirements"
	6. Далее можно нажать запустить проект
	7. Для логина надо сначала добавить пользователей. Для этого надо хотяб один раз запустить проект чтобы создался файл users.db с таблицей
