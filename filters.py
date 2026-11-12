"""Фильтры: пропускают сообщение в обработчик, только если условие выполнено."""

from aiogram.filters import BaseFilter
from aiogram.types import Message

import database as db


class IsRegistered(BaseFilter):
    """Пользователь прошёл регистрацию."""
    async def __call__(self, message: Message) -> bool:
        return db.is_registered(message.from_user.id)


class IsAdmin(BaseFilter):
    """Пользователь вошёл в админку."""
    async def __call__(self, message: Message) -> bool:
        return db.is_admin(message.from_user.id)
