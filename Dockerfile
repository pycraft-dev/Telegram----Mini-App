FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код проекта
COPY . .

# Создаем директорию для данных (БД и фото)
RUN mkdir -p /app/data/photos

# Запускаем API в фоне (порт 8000) и бота на переднем плане
# Это позволяет запустить оба процесса в одном контейнере (идеально для Amvera)
CMD uvicorn api.main:app --host 0.0.0.0 --port 8000 & python main.py
