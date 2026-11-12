"""
ГЛАВНЫЙ ФАЙЛ — запускай его (в PyCharm: правый клик -> Run 'bot').

Структура проекта:
  bot.py                  - запуск бота (этот файл)
  config.py               - токен, пароли, настройки
  database.py             - база данных SQLite
  text_check.py           - проверка текста (Участник 2)
  states.py               - шаги диалога (регистрация, админка)
  filters.py              - фильтры: зарегистрирован? админ?
  keyboards.py            - кнопки
  services/analyzer.py    - анализ и отчёты, подключение модулей команды
  services/password.py    - правила пароля (как Gmail/Apple) и шифрование
  services/antiflood.py   - защита от спама (антифлуд)
  handlers/registration.py - регистрация (/start)
  handlers/admin.py        - админка (/adminsalim)
  handlers/check.py        - проверка текста и файлов
"""

import asyncio
import logging
import os

# PyCharm на Mac не видит программы из Homebrew (ffmpeg, deno, node).
# Добавляем их папки в PATH, чтобы yt-dlp мог скачивать видео с YouTube.
import sys

# Python с python.org на Mac не знает сертификаты сайтов -> ошибка
# CERTIFICATE_VERIFY_FAILED при скачивании моделей (EasyOCR и др.).
# Берём сертификаты из пакета certifi.
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())
except ImportError:
    pass

# Если все модели уже скачаны — работаем без обращения к huggingface.co.
# Иначе при плохом интернете бот при запуске долго "стучится" туда и пишет ошибки.
_hub = os.path.expanduser("~/.cache/huggingface/hub")
_models = ["models--cointegrated--rubert-tiny-toxicity",
           "models--Falconsai--nsfw_image_detection",
           "models--openai--clip-vit-base-patch32"]
try:
    from config import WHISPER_MODEL as _wm   # модель Whisper тоже должна быть скачана
    _models.append(f"models--Systran--faster-whisper-{_wm}")
except Exception:
    pass
if all(os.path.isdir(os.path.join(_hub, m)) for m in _models):
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

# Папка Python-окружения тоже: там лежит deno, установленный через pip.
for _p in (os.path.dirname(sys.executable), "/opt/homebrew/bin", "/usr/local/bin"):
    if os.path.isdir(_p) and _p not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _p + os.pathsep + os.environ.get("PATH", "")

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

import config
import database as db
from handlers import admin, check, registration
from services.analyzer import warm_up
from services.antiflood import AntiFloodMiddleware


async def main():
    logging.basicConfig(level=logging.INFO)

    # Подготовка: база данных и папка для файлов
    db.init_db()
    os.makedirs(config.MEDIA_DIR, exist_ok=True)

    print("Загружаю модель...")
    await asyncio.to_thread(warm_up)

    bot = Bot(config.TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # Антифлуд: работает раньше всех обработчиков
    antiflood = AntiFloodMiddleware()
    dp.message.outer_middleware(antiflood)
    dp.callback_query.outer_middleware(antiflood)

    # Порядок важен: check подключается последним,
    # потому что в нём ответ "Сначала зарегистрируйся" для всех остальных сообщений
    dp.include_router(admin.router)
    dp.include_router(registration.router)
    dp.include_router(check.router)

    # Описание бота в пустом чате (до нажатия /start) и в профиле
    # Telegram сам показывает описание на языке приложения человека:
    # русский интерфейс -> ru, английский -> en, остальные -> қазақша
    from aiogram.types import BotCommand
    from i18n import t
    try:
        for code, lang in ((None, "kk"), ("ru", "ru"), ("en", "en")):
            await bot.set_my_description(t("welcome", lang), language_code=code)
            await bot.set_my_short_description(t("short_description", lang), language_code=code)
        await bot.set_my_commands([
            BotCommand(command="start", description="Бастау / Начать / Start"),
            BotCommand(command="language", description="Тіл / Язык / Language"),
        ])
    except Exception as e:
        logging.warning(f"Описание бота не обновлено: {e}")

    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
