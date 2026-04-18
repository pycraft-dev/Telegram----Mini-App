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

# Запускаем от непривилегированного пользователя (опционально, но рекомендуется)
# RUN useradd -m botuser && chown -R botuser:botuser /app
# USER botuser

CMD ["python", "main.py"]
