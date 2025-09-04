FROM python:3.11-slim-bullseye

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Создаём рабочую директорию
WORKDIR /web

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ВСЕ файлы
COPY . .
RUN ls -lah /web
# Создаём директории для логов и вывода если их нет
RUN mkdir -p logs output

# Запуск скрипта
CMD ["python", "web/webServer.py"]