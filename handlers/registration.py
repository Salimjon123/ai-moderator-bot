"""
Старт и регистрация:
/start -> выбор языка (қазақша / русский / English) -> приветствие
       -> имя -> придумать пароль -> повторить пароль -> номер телефона.
Дальше бот отвечает на выбранном языке. Сменить язык: /language.
Пароль проверяется по правилам, как в Gmail / Apple (см. services/password.py).
"""

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import config
import database as db
from i18n import LANGS, contact_keyboard, lang_keyboard, t
from keyboards import remove_kb
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


def lang_of(message_or_callback) -> str:
    return db.get_lang(message_or_callback.from_user.id)


# ================== Старт и выбор языка ==================
@router.message(CommandStart())
@router.message(Command("language", "lang"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(t("lang_choose", "ru"), reply_markup=lang_keyboard())


@router.callback_query(F.data.startswith("lang:"))
async def choose_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split(":", 1)[1]
    if lang not in LANGS:
        await callback.answer()
        return
    uid = callback.from_user.id
    db.set_lang(uid, lang)
    await callback.answer()
    await callback.message.edit_text(t("lang_set", lang))   # убираем кнопки

    # Приветствие на выбранном языке
    await callback.message.answer(t("welcome", lang), reply_markup=remove_kb)

    # Уже зарегистрирован — можно сразу отправлять контент
    if db.is_registered(uid):
        await state.clear()
        user = db.get_user(uid)
        await callback.message.answer(t("welcome_back", lang, name=esc(user["name"])))
        return

    # Шаг 1: имя
    await state.set_state(Reg.name)
    await callback.message.answer(t("reg_step1", lang))


# ================== Регистрация ==================
@router.message(Reg.name, F.text)
async def reg_name(message: Message, state: FSMContext):
    lang = lang_of(message)
    name = message.text.strip()[:50]
    await state.update_data(name=name)

    # Шаг 2: пароль
    await state.set_state(Reg.password)
    await message.answer(t("reg_step2", lang, name=esc(name), min=config.PASSWORD_MIN_LENGTH))


@router.message(Reg.password, F.text)
async def reg_password(message: Message, state: FSMContext):
    lang = lang_of(message)
    password = message.text
    await delete_quietly(message)
    data = await state.get_data()

    # Проверка по правилам — показываем, что именно не так
    if not is_strong(password, data.get("name", "")):
        await message.answer(rules_message(password, data.get("name", ""), lang))
        return  # остаёмся на этом шаге

    # Шаг 3: повтор пароля (как в Gmail — чтобы не ошибиться)
    await state.update_data(password_hash=hash_password(password),
                            password_plain=password)
    await state.set_state(Reg.password_confirm)
    await message.answer(t("pw_ok", lang))


@router.message(Reg.password_confirm, F.text)
async def reg_password_confirm(message: Message, state: FSMContext):
    lang = lang_of(message)
    await delete_quietly(message)
    data = await state.get_data()

    if message.text != data.get("password_plain"):
        # Не совпало — придумываем заново
        await state.update_data(password_hash=None, password_plain=None)
        await state.set_state(Reg.password)
        await message.answer(t("pw_mismatch", lang))
        return

    # Открытый пароль больше не нужен — убираем из памяти
    await state.update_data(password_plain=None)

    # Шаг 4: телефон
    await state.set_state(Reg.phone)
    await message.answer(t("pw_match", lang), reply_markup=contact_keyboard(lang))


@router.message(Reg.phone, F.contact)
async def reg_phone(message: Message, state: FSMContext):
    lang = lang_of(message)
    # Проверяем, что человек отправил СВОЙ номер, а не чужой контакт
    if message.contact.user_id != message.from_user.id:
        await message.answer(t("own_phone", lang), reply_markup=contact_keyboard(lang))
        return

    data = await state.get_data()
    u = message.from_user
    db.add_user(u.id, u.username, u.full_name, data["name"],
                message.contact.phone_number, data["password_hash"])
    await state.clear()
    await message.answer(t("reg_done", lang), reply_markup=remove_kb)


@router.message(Reg.phone)
async def reg_phone_wrong(message: Message):
    lang = lang_of(message)
    await message.answer(t("press_phone", lang), reply_markup=contact_keyboard(lang))


@router.message(Reg.name)
@router.message(Reg.password)
@router.message(Reg.password_confirm)
async def reg_need_text(message: Message):
    await message.answer(t("need_text", lang_of(message)))
