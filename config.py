import os
import sys
import argparse

# ========================
# КОНФИГУРАЦИЯ БОТА
# ========================

# Парсим аргументы командной строки
parser = argparse.ArgumentParser()
parser.add_argument('--token', type=str, default=None, help='Токен бота от @BotFather')
parser.add_argument('--admin', type=int, default=None, help='ID владельца от @userinfobot')
args, _ = parser.parse_known_args()

# Приоритет: аргументы командной строки → переменные окружения → значения по умолчанию
BOT_TOKEN = args.token or os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_ЗДЕСЬ")
ADMIN_ID = args.admin or int(os.getenv("ADMIN_ID", "123456789"))

DB_NAME = "anon_messages.db"
MAX_MESSAGE_LENGTH = 4000
