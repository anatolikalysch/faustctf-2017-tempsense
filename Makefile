#!/usr/bin/make -f

USER    ?= tempsense
HOME    ?= /srv/tempsense

build:
	$(MAKE) -C src

install:
	# install -m 700 -o $(USER) -d $(HOME)/data
	install -m 755 -o root src/ServiceLogic.py $(HOME)
	install -m 644 -o root src/datatypes.py $(HOME)
	install -m 755 -o root src/secure.py $(HOME)
	install -m 644 -o root src/tech_support.py $(HOME)
	install -m 755 -o root src/nltk_data.zip $(HOME)
	install -m 755 -o root src/bot_speech.zip $(HOME)
	install -m 644 -o root src/BotTemplate.py $(HOME)
	install -m 644 -o root src/BroBot.py $(HOME)
	install -m 644 -o root src/LazyBot.py $(HOME)
	install -m 644 -o root src/SupervisorBot.py $(HOME)
	install -m 644 -o root src/JokerBot.py $(HOME)
	install -m 644 -o root src/BroBot.py $(HOME)
	install -m 755 -o root src/secWrap.py $(HOME)
	cython3 --embed -o src/secure.c src/secure.py
	gcc -Os -I /usr/include/python3.4m -o src/secure src/secure.c -lpython3.4m -lpthread -lm -lutil -ldl
	install -m 755 -o root src/secure $(HOME)
	install -m 644 -o root src/tempsense.service /etc/systemd/system
	python3 -m venv --without-pip $(HOME)/venv # without pip due to pyvenv bug: [1]
	(source $(HOME)/venv/bin/activate; curl https://bootstrap.pypa.io/get-pip.py | python3 && pip3 install textblob && pip3 install PyCrypto)
	systemctl enable tempsense.service
