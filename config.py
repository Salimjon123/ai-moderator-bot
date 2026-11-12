# ===== Настройки бота =====
# Все настройки в одном месте. Меняй только здесь.

# Токен от @BotFather (старый нужно отозвать через /revoke и вставить новый)
TOKEN = ""  # настоящий токен — в config_local.py (его нет на GitHub)

# Минимальная длина пароля, который пользователь придумывает при регистрации
PASSWORD_MIN_LENGTH = 8

# Вход в админку: /adminsalim -> пароль
ADMIN_COMMAND = "adminsalim"
ADMIN_PASSWORD = "123"

# Файл базы данных и папка для сохранённых видео/аудио
DB_PATH = "bot.db"
MEDIA_DIR = "media"

# Telegram даёт ботам скачивать файлы только до 20 МБ
MAX_FILE_SIZE = 20 * 1024 * 1024

# Ключ Google Gemini для проверки кадров видео (vision_check.py).
# Пусто = проверка кадров отключена, всё остальное работает.
GEMINI_API_KEY = ""

# Языки, которые принимает бот: казахский, русский, английский
ALLOWED_LANGUAGES = ("kk", "ru", "en")

# Модель Whisper для распознавания речи.
# "small" намного лучше понимает казахский, чем "base" (скачивается один раз, ~460 МБ).
WHISPER_MODEL = "small"

# ===== Секреты =====
# Токен и ключи лежат в config_local.py — этот файл НЕ загружается на GitHub
# (он в .gitignore). Чтобы запустить бота на другом компьютере, создай
# config_local.py рядом с этим файлом и напиши в нём:
#   TOKEN = "токен от @BotFather"
try:
    from config_local import *  # noqa: F401,F403
except ImportError:
    pass

if not TOKEN:
    raise SystemExit("Нет токена! Создай файл config_local.py и напиши в нём: TOKEN = \"...\"")
