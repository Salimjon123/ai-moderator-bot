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
from i18n import t

router = Router()


# ================== Текст ==================
# Ссылки на видео, которые бот умеет скачивать
VIDEO_LINK = re.compile(
    r"https?://(?:www\.|m\.|vm\.|vt\.)?(?:youtube\.com|youtu\.be|tiktok\.com|instagram\.com)/\S+",
    re.I)


@router.message(StateFilter(None), IsRegistered(), F.text)
async def handle_text(message: Message):
    lang = db.get_lang(message.from_user.id)
    link = VIDEO_LINK.search(message.text)

    # Ссылка на видео -> скачиваем и проверяем целиком
    if link:
        wait = await message.answer(t("wait_link", lang))
        try:
            meta = {}
            parts = await analyze_link(message.from_user.id, link.group(0), meta)
            kb = None
            if meta.get("video_path"):
                # Скачать предлагаем всегда; если видео опасное — с предупреждением
                if meta.get("danger"):
                    parts.append(t("dl_ask_danger", lang))
                    text = t("dl_btn_danger", lang)
                else:
                    parts.append(t("dl_ask_safe", lang))
                    text = t("dl_btn_safe", lang)
                kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
                    text=text, callback_data=f"dl:{meta['media_id']}")]])
            else:
                parts.append(t("dl_unavailable", lang))
            await wait.edit_text("\n\n".join(parts)[:4000], reply_markup=kb)
        except Exception as e:
            logging.exception("Ошибка анализа ссылки")
            await wait.edit_text(t("link_error", lang, e=esc(e)))
        return

    # Обычный текст: только казахский, русский, английский
    if detect_text_language(message.text) is None:
        await message.answer(t("lang_unsupported", lang))
        return

    wait = await message.answer(t("wait_text", lang))
    try:
        report = await analyze_text(message.from_user.id, message.text,
                                    "text", t("title_text", lang))
        await wait.edit_text(report)
    except Exception as e:
        logging.exception("Ошибка анализа текста")
        await wait.edit_text(t("error", lang, e=esc(e)))


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
    lang = db.get_lang(uid)
    kind, obj, ext = detect_media(message)
    logging.info(f"Получен файл: {kind}, размер {obj.file_size} байт, от {uid}")
    wait = await message.answer(t("wait_file", lang))

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
                                            t("title_caption", lang)))
    except Exception as e:
        logging.exception("Ошибка анализа файла")
        parts.append(t("error", lang, e=esc(e)))

    if path is None and kind in ("video", "video_note", "photo"):
        parts.insert(0, t("file_too_big", lang))
    if not parts:
        parts.append(t("file_saved", lang))
    kb = None
    if kind in ("audio", "voice") and meta.get("transcript"):
        # Спрашиваем всегда; если аудио опасное или подозрительное — с предупреждением
        if meta.get("danger"):
            parts.append(t("audio_ask_danger", lang))
        elif meta.get("suspicious"):
            parts.append(t("audio_ask_susp", lang))
        else:
            parts.append(t("audio_ask_safe", lang))
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(
            text=t("btn_show_text", lang), callback_data=f"tr:{media_id}")]])
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
    lang = db.get_lang(callback.from_user.id)
    media = _own_media(callback)
    if not media or not media["transcript"]:
        await callback.answer(t("text_not_found", lang), show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)  # убираем кнопку
    text = media["transcript"]
    for i in range(0, len(text), 3900):          # длинный текст — несколькими сообщениями
        await callback.message.answer(f"{t('transcript_head', lang)}\n\n{esc(text[i:i + 3900])}")


@router.callback_query(F.data.startswith("dl:"))
async def download_video(callback: CallbackQuery):
    lang = db.get_lang(callback.from_user.id)
    media = _own_media(callback)
    path = media["file_path"] if media else None
    if not path or not os.path.isfile(path):
        await callback.answer(t("video_not_found", lang), show_alert=True)
        return
    # Telegram даёт ботам отправлять файлы до 50 МБ
    if os.path.getsize(path) > 50 * 1024 * 1024:
        await callback.answer(t("video_too_big", lang), show_alert=True)
        return
    await callback.answer(t("sending_video", lang))
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer_video(FSInputFile(path), caption=esc(media["caption"] or ""))


# ================== Незарегистрированные ==================
@router.message(StateFilter(None))
async def not_registered(message: Message):
    await message.answer(t("not_registered", db.get_lang(message.from_user.id)))


# ================== Всё остальное ==================
@router.message()
async def unexpected(message: Message, state: FSMContext):
    """Бот ждал другое (пароль, текст рассылки...), а пришёл файл."""
    await state.clear()
    await message.answer(t("unexpected", db.get_lang(message.from_user.id)))
