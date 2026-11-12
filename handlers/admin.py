"""Админка: /adminsalim -> пароль (123) -> кнопки управления."""

import asyncio

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import config
import database as db
from filters import IsAdmin
from keyboards import (BTN_AUDIO, BTN_BROADCAST, BTN_CHECKS, BTN_DANGER,
                       BTN_EXIT, BTN_STATS, BTN_USERS, BTN_VIDEO, admin_kb,
                       remove_kb)
from services.analyzer import VERDICT_EMOJI, esc
from states import AdminLogin, Broadcast

router = Router()


# ================== Вход ==================
@router.message(Command(config.ADMIN_COMMAND))
async def admin_enter(message: Message, state: FSMContext):
    await state.set_state(AdminLogin.password)
    await message.answer("🔐 Введи пароль админа:")


@router.message(AdminLogin.password, F.text)
async def admin_password(message: Message, state: FSMContext):
    await state.clear()
    try:
        await message.delete()  # убираем пароль из чата
    except Exception:
        pass

    if message.text.strip() == config.ADMIN_PASSWORD:
        u = message.from_user
        db.set_admin(u.id, True, u.username, u.full_name)
        await message.answer("✅ Добро пожаловать в админку!", reply_markup=admin_kb)
    else:
        await message.answer("❌ Неверный пароль.")


# ================== Статистика ==================
@router.message(StateFilter(None), IsAdmin(), F.text == BTN_STATS)
async def admin_stats(message: Message):
    s = db.stats()
    m = s["media"]
    await message.answer(
        "📊 <b>Статистика</b>\n\n"
        f"👥 Пользователей: <b>{s['users']}</b>\n"
        f"📝 Проверок: <b>{s['checks']}</b>\n"
        f"🔴 Опасных: <b>{s['danger']}</b>\n"
        f"🟡 Подозрительных: <b>{s['suspicious']}</b>\n\n"
        f"🎬 Видео: {m.get('video', 0)} | Кружков: {m.get('video_note', 0)}\n"
        f"🎵 Аудио: {m.get('audio', 0)} | Голосовых: {m.get('voice', 0)}\n"
        f"🖼 Фото: {m.get('photo', 0)} | Документов: {m.get('document', 0)}")


# ================== Пользователи ==================
@router.message(StateFilter(None), IsAdmin(), F.text == BTN_USERS)
async def admin_users(message: Message):
    users = db.list_users(20)
    if not users:
        await message.answer("Пользователей пока нет.")
        return

    lines = ["👥 <b>Последние 20 пользователей:</b>\n"]
    for u in users:
        uname = f"@{u['username']}" if u["username"] else "—"
        crown = " 👑" if u["is_admin"] else ""
        lines.append(
            f"• <b>{esc(u['name'] or u['full_name'])}</b>{crown} {esc(uname)}\n"
            f"  ID: <code>{u['user_id']}</code> | 📱 {esc(u['phone'] or '—')}\n"
            f"  {u['registered_at']}")
    await message.answer("\n".join(lines)[:4000])


# ================== Проверки ==================
async def show_checks(message: Message, only_danger: bool):
    rows = db.last_checks(10, only_danger)
    if not rows:
        await message.answer("Проверок пока нет.")
        return

    title = "🔴 <b>Последние опасные:</b>" if only_danger else "📝 <b>Последние проверки:</b>"
    lines = [title + "\n"]
    for c in rows:
        lines.append(
            f"{VERDICT_EMOJI.get(c['verdict'], '⚪')} {c['toxicity']}% — "
            f"<b>{esc(c['name'] or c['user_id'])}</b> ({c['kind']}, {c['created_at']})\n"
            f"  <i>{esc((c['content'] or '')[:100])}</i>")
    await message.answer("\n".join(lines)[:4000])


@router.message(StateFilter(None), IsAdmin(), F.text == BTN_CHECKS)
async def admin_checks(message: Message):
    await show_checks(message, only_danger=False)


@router.message(StateFilter(None), IsAdmin(), F.text == BTN_DANGER)
async def admin_danger(message: Message):
    await show_checks(message, only_danger=True)


# ================== Видео и аудио ==================
async def send_media_row(message: Message, row):
    """Пересылает админу сохранённый файл по его file_id."""
    caption = f"от {esc(row['name'] or row['user_id'])}, {row['created_at']}"
    kind, fid = row["kind"], row["file_id"]
    try:
        if kind == "video":
            await message.answer_video(fid, caption=caption)
        elif kind == "video_note":
            await message.answer_video_note(fid)
            await message.answer(caption)
        elif kind == "audio":
            await message.answer_audio(fid, caption=caption)
        elif kind == "voice":
            await message.answer_voice(fid, caption=caption)
    except Exception as e:
        await message.answer(f"Не удалось отправить файл: {esc(e)}")


@router.message(StateFilter(None), IsAdmin(), F.text == BTN_VIDEO)
async def admin_video(message: Message):
    rows = db.last_media(("video", "video_note"), 5)
    if not rows:
        await message.answer("Видео пока нет.")
    for r in rows:
        await send_media_row(message, r)


@router.message(StateFilter(None), IsAdmin(), F.text == BTN_AUDIO)
async def admin_audio(message: Message):
    rows = db.last_media(("audio", "voice"), 5)
    if not rows:
        await message.answer("Аудио пока нет.")
    for r in rows:
        await send_media_row(message, r)


# ================== Рассылка ==================
@router.message(StateFilter(None), IsAdmin(), F.text == BTN_BROADCAST)
async def admin_broadcast_start(message: Message, state: FSMContext):
    await state.set_state(Broadcast.text)
    await message.answer("📢 Напиши текст рассылки (или «отмена»):")


@router.message(Broadcast.text, F.text)
async def admin_broadcast_send(message: Message, state: FSMContext):
    await state.clear()
    if message.text.strip().lower() == "отмена":
        await message.answer("Рассылка отменена.", reply_markup=admin_kb)
        return

    ok = fail = 0
    for uid in db.all_user_ids():
        try:
            await message.bot.send_message(uid, f"📢 {esc(message.text)}")
            ok += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)  # пауза, чтобы Telegram не заблокировал за спам
    await message.answer(f"✅ Отправлено: {ok}, не доставлено: {fail}",
                         reply_markup=admin_kb)


# ================== Выход ==================
@router.message(StateFilter(None), IsAdmin(), F.text == BTN_EXIT)
async def admin_exit(message: Message):
    db.set_admin(message.from_user.id, False)
    await message.answer("Ты вышел из админки.", reply_markup=remove_kb)
