"""
Регистрация: /start -> имя -> придумать пароль -> повторить пароль -> номер телефона.
Пароль проверяется по правилам, как в Gmail / Apple (см. services/password.py).
"""

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import config
import database as db
from keyboards import contact_kb, remove_kb
from services.analyzer import esc
from services.password import hash_password, is_strong, rules_message
from states import Reg

router = Router()


async def delete_quietly(message: Message):
    """Удаляет сообщение с паролем, чтобы его не было видно в чате."""
    try:
        await message.delete()
    except Exception:
        pass


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()

    # Уже зарегистрирован — просто здороваемся
    if db.is_registered(message.from_user.id):
        user = db.get_user(message.from_user.id)
        await message.answer(
            f"👋 С возвращением, {esc(user['name'])}!\n"
            "Отправь текст, видео или аудио — я проверю его.",
            reply_markup=remove_kb)
        return

    # Шаг 1: имя
    await state.set_state(Reg.name)
    await message.answer("👋 Привет! Давай зарегистрируемся.\n\n"
                         "<b>Шаг 1 из 4.</b> Как тебя зовут?",
                         reply_markup=remove_kb)


@router.message(Reg.name, F.text)
async def reg_name(message: Message, state: FSMContext):
    name = message.text.strip()[:50]
    await state.update_data(name=name)

    # Шаг 2: пароль
    await state.set_state(Reg.password)
    await message.answer(
        f"Приятно познакомиться, {esc(name)}!\n\n"
        "<b>Шаг 2 из 4.</b> Придумай пароль.\n\n"
        "Требования:\n"
        f"• не меньше {config.PASSWORD_MIN_LENGTH} символов\n"
        "• хотя бы одна цифра\n"
        "• хотя бы одна заглавная и одна строчная английская буква\n"
        "• без русских букв и пробелов\n\n"
        "Пример: <code>Salem2026!</code> (придумай свой)\n"
        "🔒 Сообщение с паролем я сразу удалю из чата.")


@router.message(Reg.password, F.text)
async def reg_password(message: Message, state: FSMContext):
    password = message.text
    await delete_quietly(message)
    data = await state.get_data()

    # Проверка по правилам — показываем, что именно не так
    if not is_strong(password, data.get("name", "")):
        await message.answer(rules_message(password, data.get("name", "")))
        return  # остаёмся на этом шаге

    # Шаг 3: повтор пароля (как в Gmail — чтобы не ошибиться)
    await state.update_data(password_hash=hash_password(password),
                            password_plain=password)
    await state.set_state(Reg.password_confirm)
    await message.answer("✅ Надёжный пароль!\n\n"
                         "<b>Шаг 3 из 4.</b> Введи пароль ещё раз:")


@router.message(Reg.password_confirm, F.text)
async def reg_password_confirm(message: Message, state: FSMContext):
    await delete_quietly(message)
    data = await state.get_data()

    if message.text != data.get("password_plain"):
        # Не совпало — придумываем заново
        await state.update_data(password_hash=None, password_plain=None)
        await state.set_state(Reg.password)
        await message.answer("❌ Пароли не совпадают.\n\n"
                             "Придумай пароль заново (шаг 2 из 4):")
        return

    # Открытый пароль больше не нужен — убираем из памяти
    await state.update_data(password_plain=None)

    # Шаг 4: телефон
    await state.set_state(Reg.phone)
    await message.answer("✅ Пароли совпадают!\n\n"
                         "<b>Шаг 4 из 4.</b> Нажми кнопку ниже, "
                         "чтобы отправить номер телефона.",
                         reply_markup=contact_kb)


@router.message(Reg.phone, F.contact)
async def reg_phone(message: Message, state: FSMContext):
    # Проверяем, что человек отправил СВОЙ номер, а не чужой контакт
    if message.contact.user_id != message.from_user.id:
        await message.answer("Отправь, пожалуйста, свой номер через кнопку.",
                             reply_markup=contact_kb)
        return

    data = await state.get_data()
    u = message.from_user
    db.add_user(u.id, u.username, u.full_name, data["name"],
                message.contact.phone_number, data["password_hash"])
    await state.clear()

    await message.answer(
        "🎉 Регистрация завершена!\n\n"
        "Теперь отправь мне:\n"
        "• текст или комментарии (каждый с новой строки)\n"
        "• видео или кружок\n"
        "• аудио или голосовое\n\n"
        "Я проверю их на буллинг, мат, угрозы и нелегал.",
        reply_markup=remove_kb)


@router.message(Reg.phone)
async def reg_phone_wrong(message: Message):
    await message.answer("Нажми кнопку «📱 Отправить номер».", reply_markup=contact_kb)


@router.message(Reg.name)
@router.message(Reg.password)
@router.message(Reg.password_confirm)
async def reg_need_text(message: Message):
    await message.answer("Отправь, пожалуйста, текстом.")
