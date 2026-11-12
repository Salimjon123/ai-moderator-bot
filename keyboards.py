"""Клавиатуры (кнопки под полем ввода)."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

# Убрать клавиатуру
remove_kb = ReplyKeyboardRemove()

# Кнопка "Отправить номер" при регистрации
contact_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📱 Отправить номер", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

# Тексты кнопок админки
BTN_STATS = "📊 Статистика"
BTN_USERS = "👥 Пользователи"
BTN_CHECKS = "📝 Последние проверки"
BTN_DANGER = "🔴 Опасные"
BTN_VIDEO = "🎬 Видео"
BTN_AUDIO = "🎵 Аудио"
BTN_BROADCAST = "📢 Рассылка"
BTN_EXIT = "🚪 Выйти из админки"

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_STATS), KeyboardButton(text=BTN_USERS)],
        [KeyboardButton(text=BTN_CHECKS), KeyboardButton(text=BTN_DANGER)],
        [KeyboardButton(text=BTN_VIDEO), KeyboardButton(text=BTN_AUDIO)],
        [KeyboardButton(text=BTN_BROADCAST), KeyboardButton(text=BTN_EXIT)],
    ],
    resize_keyboard=True,
)
