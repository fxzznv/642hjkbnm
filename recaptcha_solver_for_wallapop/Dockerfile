FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Создаём рабочую директорию
WORKDIR /capsolver

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y curl

# Копируем ВСЕ файлы, включая .env
COPY . .

# Запуск скрипта
CMD ["python", "cap_solver.py"]