# 🚀 Руководство по деплою (развертыванию) на VPS

Для работы Telegram Mini App **обязательно** нужен HTTPS. Поэтому вам понадобится домен (или поддомен) и сервер (VPS).

## 🛠 Шаг 1. Подготовка сервера
1. Арендуйте любой недорогой VPS (Ubuntu 22.04 или 24.04). Хватит 1 vCPU и 1 ГБ RAM.
2. Привяжите ваш домен (например, `app.yourdomain.com`) к IP-адресу сервера (A-запись в панели управления доменом).
3. Подключитесь к серверу по SSH:
   ```bash
   ssh root@ip_вашего_сервера
   ```

## 🐳 Шаг 2. Установка Docker
Выполните на сервере команды для установки Docker и Docker Compose:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

## 📂 Шаг 3. Перенос проекта на сервер
Скопируйте файлы проекта на сервер (например, через FileZilla, WinSCP или `scp`).
Или загрузите проект на GitHub и сделайте `git clone` на сервере.

Перейдите в папку с проектом на сервере:
```bash
cd /path/to/your/project
```

## ⚙️ Шаг 4. Настройка .env
Создайте или отредактируйте файл `.env` на сервере:
```bash
nano .env
```
Укажите ваши реальные данные. **Важно:** `WEBAPP_URL` должен быть вашим доменом с `https://`.
```ini
BOT_TOKEN=ваш_токен_бота
SECRET_KEY=длинный_случайный_ключ
WEBAPP_URL=https://app.yourdomain.com
ADMIN_IDS=ваш_id
# Для продакшена лучше отключить SQL_ECHO
SQL_ECHO=false
```

## 🚀 Шаг 5. Запуск через Docker Compose
В корне проекта (где лежит `docker-compose.yml`) выполните:
```bash
docker compose up -d --build
```
*Docker сам скачает Python, установит зависимости и запустит два контейнера: бота и API. База данных и картинки будут сохраняться в папке `data/` рядом с проектом.*

## 🔒 Шаг 6. Настройка Nginx и HTTPS (Let's Encrypt)
Так как API работает на порту 8000 (HTTP), нам нужен Nginx, чтобы принимать HTTPS-запросы и перенаправлять их в API.

1. Установите Nginx и Certbot:
   ```bash
   apt update
   apt install nginx certbot python3-certbot-nginx -y
   ```

2. Создайте конфигурацию Nginx для вашего домена:
   ```bash
   nano /etc/nginx/sites-available/bot_app
   ```
   Вставьте следующий код (заменив `app.yourdomain.com` на ваш домен):
   ```nginx
   server {
       listen 80;
       server_name app.yourdomain.com;

       location / {
           proxy_pass http://127.0.0.0:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. Включите конфигурацию и перезапустите Nginx:
   ```bash
   ln -s /etc/nginx/sites-available/bot_app /etc/nginx/sites-enabled/
   nginx -t
   systemctl reload nginx
   ```

4. Выпустите бесплатный SSL-сертификат:
   ```bash
   certbot --nginx -d app.yourdomain.com
   ```
   *Certbot автоматически настроит HTTPS в вашем файле конфигурации.*

🎉 **Готово!** Теперь ваш бот и Mini App работают на сервере 24/7.
Для просмотра логов используйте:
```bash
docker compose logs -f
```
