# device_monitoring
﻿# <a name="_28npfxije271"></a>**Документация проекта: Device Monitoring API**
## <a name="_5msezrdly27q"></a>**📖 Описание проекта**
**Device Monitoring API** — это система сбора характеристик компьютеров, работающих в сети, и их сохранения в базе данных. Агент устанавливается на устройства, собирает данные о системе и отправляет их на сервер с REST API, который хранит их в PostgreSQL.

-----
## <a name="_qa4juw1rtpn7"></a>**📐 Архитектура**
### <a name="_x8uyrv162w3g"></a>**🖥 Компоненты**
1. **Агент** (Python-скрипт):
   1. Запускается на каждом компьютере.
   1. Считывает характеристики системы (CPU, RAM, OS и т. д.).
   1. Отправляет данные на сервер.
1. **Сервер (Flask API)**:
   1. Принимает данные от агентов.
   1. Сохраняет их в PostgreSQL.
   1. Предоставляет REST API для работы с данными.
1. **База данных (PostgreSQL)**:
   1. Хранит информацию о устройствах.
-----
## <a name="_rg5sm4gm8qiq"></a>**📦 Установка и настройка**
### <a name="_tnfm3ekwut84"></a>**1️⃣ Установка сервера**
#### <a name="_h9tobvtcdtqs"></a>**📌 Требования:**
- Python 3.8+
- PostgreSQL
- pip install flask psycopg2 requests flask-tls
#### <a name="_dr0ucrvcmzb3"></a>**📌 Настройка PostgreSQL**
CREATE DATABASE device\_monitoring;

CREATE USER monitoring\_user WITH ENCRYPTED PASSWORD 'secure\_password';

GRANT ALL PRIVILEGES ON DATABASE device\_monitoring TO monitoring\_user;

-----
### <a name="_tyv69q6u56ui"></a>**2️⃣ Установка агента**
#### <a name="_53ett2ongrdk"></a>**📌 Требования:**
- Python 3.8+
- pip install requests psutil
#### <a name="_tuxha3u8ufk"></a>**📌 Настройка клиента:**
1. Копируем agent.py на клиентские компьютеры.
1. В SERVER\_URL указываем IP сервера.
1. Запускаем агент.

python agent.py

Для автоматического запуска агента при старте системы:

- **Windows**: добавляем .bat-файл в автозагрузку.
- **Linux**: создаем systemd-сервис:

sudo nano /etc/systemd/system/device\_agent.service

[Unit]

Description=Device Monitoring Agent

After=network.target

[Service]

ExecStart=/usr/bin/python3 /path/to/agent.py

Restart=always

[Install]

WantedBy=multi-user.target

sudo systemctl enable device\_agent

sudo systemctl start device\_agent

#### <a name="_v1p7tp5qhruc"></a>**📌 Запуск агента раз в день в 10:00 (или сразу при включении ноутбука, если пропущен запуск)**
Для **Linux** (через systemd таймер):

sudo nano /etc/systemd/system/device\_agent.timer

[Unit]

Description=Run Device Monitoring Agent daily at 10:00 AM

[Timer]

OnCalendar=\*-\*-\* 10:00:00

Persistent=true

[Install]

WantedBy=timers.target

sudo systemctl enable device\_agent.timer

sudo systemctl start device\_agent.timer

Для **Windows**:

1. Открыть "Планировщик заданий".
1. Создать новую задачу.
1. В триггере выбрать "Ежедневно" в 10:00.
1. В параметрах установить "Запускать задачу, если пропущено выполнение".
1. В действии выбрать запуск python.exe с аргументом C:\path\to\agent.py.
-----
## <a name="_izllcyowmgnr"></a>**🔥 API эндпоинты**
### <a name="_3085x6881yay"></a>**📤 1. Отправка данных с клиента**
POST /report
#### <a name="_cbboal1osmf8"></a>**🔹 Запрос (JSON):**
{

`  `"owner": "user1",

`  `"internal\_ip": "192.168.1.10",

`  `"cpu": "Intel i7",

`  `"ram": "16GB",

`  `"os": "Windows 10"

}

#### <a name="_ncjzm52zscki"></a>**🔹 Ответ:**
{

`  `"status": "success",

`  `"message": "Device info saved"

}

### <a name="_rczecugw11rd"></a>**📥 2. Получение списка устройств**
GET /devices
#### <a name="_i52xocmlm3i1"></a>**🔹 Ответ:**
[

`  `{

`    `"id": 1,

`    `"owner": "user1",

`    `"cpu": "Intel i7",

`    `"ram": "16GB"

`  `}

]

-----
## <a name="_dxglyedrz503"></a>**🔒 Безопасность**
1. **Защита БД**:
   1. Создаём отдельного пользователя с ограниченными правами.
