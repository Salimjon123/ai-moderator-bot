"""Состояния (шаги диалога). Бот запоминает, на каком шаге находится пользователь."""

from aiogram.fsm.state import State, StatesGroup


class Reg(StatesGroup):
    """Регистрация: имя -> пароль -> повтор пароля -> телефон."""
    name = State()
    password = State()
    password_confirm = State()
    phone = State()


class AdminLogin(StatesGroup):
    """Вход в админку: ожидаем пароль."""
    password = State()


class Broadcast(StatesGroup):
    """Рассылка: ожидаем текст сообщения."""
    text = State()
