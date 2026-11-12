"""
Антифлуд: защита бота от спама.

Правила (числа меняются в config.py):
  • больше FLOOD_LIMIT сообщений за FLOOD_WINDOW секунд
      -> бот предупреждает и FLOOD_MUTE секунд не отвечает этому человеку;
  • тяжёлая проверка (видео, аудио, фото, ссылка) — только одна за раз:
      пока идёт прошлая, новая не запускается.
Админов антифлуд не трогает.
"""

import re
import time
from collections import defaultdict, deque

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

import config
import database as db
from i18n import t

VIDEO_LINK = re.compile(
    r"https?://(?:www\.|m\.|vm\.|vt\.)?(?:youtube\.com|youtu\.be|tiktok\.com|instagram\.com)/\S+",
    re.I)


def is_heavy(message: Message) -> bool:
    """Проверка, которая долго грузит компьютер: файлы и ссылки на видео."""
    if (message.video or message.video_note or message.audio or message.voice
            or message.photo or message.document or message.animation):
        return True
    return bool(message.text and VIDEO_LINK.search(message.text))


class AntiFloodMiddleware(BaseMiddleware):
    def __init__(self):
        self.hits = defaultdict(deque)   # user_id -> время последних сообщений
        self.muted_until = {}            # user_id -> до какого времени молчим
        self.busy = set()                # у кого сейчас идёт тяжёлая проверка

    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user is None or db.is_admin(user.id):
            return await handler(event, data)

        uid, now = user.id, time.monotonic()

        # 1) Человек в "муте" — молча игнорируем
        if self.muted_until.get(uid, 0) > now:
            return

        # 2) Считаем сообщения за последние FLOOD_WINDOW секунд
        q = self.hits[uid]
        q.append(now)
        while q and now - q[0] > config.FLOOD_WINDOW:
            q.popleft()
        if len(q) > config.FLOOD_LIMIT:
            q.clear()
            self.muted_until[uid] = now + config.FLOOD_MUTE
            await _reply(event, t("flood", db.get_lang(uid), sec=config.FLOOD_MUTE))
            return

        # 3) Тяжёлая проверка — только одна за раз
        if isinstance(event, Message) and is_heavy(event):
            if uid in self.busy:
                await _reply(event, t("busy", db.get_lang(uid)))
                return
            self.busy.add(uid)
            try:
                return await handler(event, data)
            finally:
                self.busy.discard(uid)

        return await handler(event, data)


async def _reply(event, text: str):
    if isinstance(event, CallbackQuery):
        await event.answer(text, show_alert=True)
    elif isinstance(event, Message):
        await event.answer(text)
