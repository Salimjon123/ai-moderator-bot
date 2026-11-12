"""Проверка контента: текст, видео, аудио, фото. Только для зарегистрированных."""

import logging
import os
import re
import time

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (CallbackQuery, FSInputFile, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)

import config
import database as db
from filters import IsRegistered
from services.analyzer import analyze_file, analyze_link, analyze_text, esc
from services.language import detect_text_language

router = Router()


# ================== Текст ==================
# Ссылки на видео, которые бот умеет скачивать
VIDEO_LINK = re.compile(
    r"https?://(?:www\.|m\.|vm\.|vt\.)?(?:youtube\.com|youtu\.be|tiktok\.com|instagram\.com)/\S+",
    re.I)


@router.message(StateFilter(None), IsRegistered(), F.text)
async def handle_text(message: Message):
    link = VIDEO_LINK.search(message.text)

    # Ссылка на видео -> скачиваем и проверяем целиком
    if link:
        wait = await message.answer("⏳ Скачиваю видео по ссылке и анализирую...\n"
                                    "Это может занять 1–3 минуты.")
        try:
            meta = {}
            parts = await analyze_link(message.from_user.id, link.group(0), meta)
            kb = None
            if meta.get("video_path") and not meta.get("danger"):
                # Безопасное видео — предлагаем скачать
                parts.append("✅ Видео безопасное. Хочешь скачать его?")
                kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
                    text="⬇️ Скачать видео", callback_data=f"dl:{meta['media_id']}")]])
            elif meta.get("danger"):
                parts.append("⛔ Видео опасное — скачивание недоступно.")
            else:
                parts.append("⬇️ Скачать это видео нельзя: бот не смог его загрузить.")
            await wait.edit_text("\n\n".join(parts)[:4000], reply_markup=kb)
        except Exception as e:
            logging.exception("Ошибка анализа ссылки")
            await wait.edit_text(f"❌ Не удалось проверить видео по ссылке: {esc(e)}")
        return

    # Обычный текст: только казахский, русский, английский
    if detect_text_language(message.text) is None:
        await message.answer(
            "🌐 Бот қазақ, орыс және ағылшын тілдерін ғана қабылдайды.\n"
            "Бот принимает только казахский, русский и английский.\n"
            "The bot accepts only Kazakh, Russian and English.")
        return

    wait = await message.answer("⏳ Анализирую...")
    try:
        report = await analyze_text(message.from_user.id, message.text,
                                    "text", "📝 Анализ текста")
        await wait.edit_text(report)
    except Exception as e:
        logging.exception("Ошибка анализа текста")
        await wait.edit_text(f"❌ Ошибка: {esc(e)}")


# ================== Файлы ==================
def detect_media(message: Message):
    """Определяет тип файла. Возвращает (тип, объект файла, расширение)."""
    def ext_of(name, default):
        return os.path.splitext(name)[1] if name and "." in name else default

    if message.video:
        return "video", message.video, ".mp4"
    if message.animation:   # короткое видео без звука (GIF/mp4)
        return "video", message.animation, ".mp4"
    if message.video_note:
        return "video_note", message.video_note, ".mp4"
    if message.audio:
        return "audio", message.audio, ext_of(message.audio.file_name, ".mp3")
    if message.voice:
        return "voice", message.voice, ".ogg"
    if message.photo:
        return "photo", message.photo[-1], ".jpg"
    if message.document:
        # Видео или фото, отправленное "как файл" (так часто делает Telegram на Mac/ПК)
        doc = message.document
        mime = (doc.mime_type or "").lower()
        if mime.startswith("video/"):
            return "video", doc, ext_of(doc.file_name, ".mp4")
        if mime.startswith("image/"):
            return "photo", doc, ext_of(doc.file_name, ".jpg")
        return "document", doc, ext_of(doc.file_name, "")
    return None, None, None


async def download(message: Message, obj, kind: str, ext: str):
    """Скачивает файл в media/<тип>/. Возвращает путь или None."""
    folder = os.path.join(config.MEDIA_DIR, kind)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{message.from_user.id}_{int(time.time())}{ext}")
    try:
        if obj.file_size and obj.file_size > config.MAX_FILE_SIZE:
            raise ValueError("файл больше 20 МБ")
        await message.bot.download(obj, destination=path)
        return path
    except Exception as e:
        logging.warning(f"Файл не скачан: {e}")
        return None


@router.message(StateFilter(None), IsRegistered(),
                F.video | F.animation | F.video_note | F.audio | F.voice | F.photo | F.document)
async def handle_media(message: Message):
    uid = message.from_user.id
    kind, obj, ext = detect_media(message)
    logging.info(f"Получен файл: {kind}, размер {obj.file_size} байт, от {uid}")
    wait = await message.answer("⏳ Получил файл. Сохраняю и анализирую...\n"
                                "Видео проверяется 30 секунд – 2 минуты.")

    # 1) Скачиваем на диск
    path = await download(message, obj, kind, ext)

    # 2) Сохраняем в базу (file_id сохраняется всегда, даже если файл большой)
    media_id = db.save_media(uid, kind, obj.file_id, path, message.caption)

    # 3) Анализируем
    parts = []
    meta = {}
    try:
        parts += await analyze_file(uid, path, kind, meta)
        if meta.get("transcript"):
            db.set_transcript(media_id, meta["transcript"])
        if message.caption:
            parts.append(await analyze_text(uid, message.caption, "caption",
                                            "💬 Анализ подписи"))
    except Exception as e:
        logging.exception("Ошибка анализа файла")
        parts.append(f"❌ Ошибка анализа: {esc(e)}")

    if path is None and kind in ("video", "video_note", "photo"):
        parts.insert(0, "⚠️ Файл больше 20 МБ — Telegram не даёт ботам скачивать такие файлы.\n"
                        "Отправь видео покороче или ссылку на YouTube/TikTok.")
    if not parts:
        parts.append("✅ Файл сохранён в базу.\nАвтоматически анализируются видео, кружки, фото, голосовые, аудио и подписи.")
    kb = None
    if kind in ("audio", "voice") and meta.get("transcript") and not meta.get("suspicious"):
        # Безопасное аудио — спрашиваем, нужен ли текст
        parts.append("✅ Аудио безопасное. Нужен текстовый вариант?")
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
            text="📝 Показать текст", callback_data=f"tr:{media_id}")]])
    await wait.edit_text("\n\n".join(parts)[:4000], reply_markup=kb)


# ================== Кнопки под ответом ==================
def _own_media(callback: CallbackQuery):
    """Достаёт файл из базы, только если он принадлежит этому пользователю (или админу)."""
    try:
        media = db.get_media(int(callback.data.split(":", 1)[1]))
    except (ValueError, IndexError):
        return None
    uid = callback.from_user.id
    if media and (media["user_id"] == uid or db.is_admin(uid)):
        return media
    return None


@router.callback_query(F.data.startswith("tr:"))
async def show_transcript(callback: CallbackQuery):
    media = _own_media(callback)
    if not media or not media["transcript"]:
        await callback.answer("Текст не найден", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)  # убираем кнопку
    text = media["transcript"]
    for i in range(0, len(text), 3900):          # длинный текст — несколькими сообщениями
        await callback.message.answer(f"📝 <b>Текст аудио:</b>\n\n{esc(text[i:i + 3900])}")


@router.callback_query(F.data.startswith("dl:"))
async def download_video(callback: CallbackQuery):
    media = _own_media(callback)
    path = media["file_path"] if media else None
    if not path or not os.path.isfile(path):
        await callback.answer("Видео не найдено на сервере", show_alert=True)
        return
    # Telegram даёт ботам отправлять файлы до 50 МБ
    if os.path.getsize(path) > 50 * 1024 * 1024:
        await callback.answer("Видео больше 50 МБ — Telegram не даёт боту его отправить",
                              show_alert=True)
        return
    await callback.answer("⏳ Отправляю видео...")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer_video(FSInputFile(path), caption=esc(media["caption"] or ""))


# ================== Незарегистрированные ==================
@router.message(StateFilter(None))
async def not_registered(message: Message):
    await message.answer("Сначала зарегистрируйся: нажми /start")


# ================== Всё остальное ==================
@router.message()
async def unexpected(message: Message, state: FSMContext):
    """Бот ждал другое (пароль, текст рассылки...), а пришёл файл."""
    await state.clear()
    await message.answer("Я ждал другой ответ, поэтому сбросил текущее действие.\n"
                         "Отправь файл ещё раз или нажми /start.")
