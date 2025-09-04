import logging
import os
from datetime import datetime
from src.mail.utils.const_mail import BASE_DIR

import logging
from datetime import datetime

def setup_logger(name):
    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Очищаем существующие обработчики, чтобы избежать дублирования
    logger.handlers.clear()

    # Создаем обработчик для вывода в терминал
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Настраиваем формат логов
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)

    # Добавляем только консольный обработчик
    logger.addHandler(console_handler)

    # Отключаем распространение логов на родительские логгеры
    logger.propagate = False

    return logger





# Путь к директории логов
LOG_DIR = os.path.join(BASE_DIR, "..", "..", "..", "logs", "program_running_logging")

def setup_logger_to_save_to_file(name):
    # Создаем директорию для логов, если она не существует
    os.makedirs(LOG_DIR, exist_ok=True)

    # Формируем путь к файлу лога
    log_file = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")

    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Очищаем существующие обработчики, чтобы избежать дублирования
    logger.handlers.clear()

    # Создаем обработчик для записи в файл
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # Настраиваем формат логов
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # Добавляем только файловый обработчик
    logger.addHandler(file_handler)

    # Отключаем распространение логов на родительские логгеры
    logger.propagate = False

    return logger