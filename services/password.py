"""
Проверка надёжности пароля (как в Gmail, Apple, Mail.ru) и его шифрование.

Правила:
  • от 8 до 64 символов
  • хотя бы одна цифра
  • хотя бы одна заглавная латинская буква (A-Z)
  • хотя бы одна строчная латинская буква (a-z)
  • только латиница, цифры и символы — без русских букв и пробелов
  • не слишком простой (не 12345678, password, qwerty123 и т.п.)
  • не совпадает с именем
"""

import hashlib
import hmac
import os
import string

import config

ALLOWED_CHARS = set(string.ascii_letters + string.digits + string.punctuation)

# Самые популярные пароли — такие взламывают за секунды
COMMON_PASSWORDS = {
    "12345678", "123456789", "1234567890", "password", "password1",
    "password123", "qwerty123", "qwertyuiop", "11111111", "00000000",
    "abc12345", "iloveyou1", "admin123", "welcome1", "qwerty12",
    "1q2w3e4r", "1q2w3e4r5t", "zaq12wsx", "asdfghjkl", "qwerty1234",
}


def check_rules(password: str, name: str = "", lang: str = "ru") -> list:
    """
    Проверяет пароль. Возвращает список правил: [(выполнено?, текст правила), ...]
    Текст правил — на языке пользователя (lang).
    """
    from i18n import t
    p = password
    return [
        (config.PASSWORD_MIN_LENGTH <= len(p) <= 64,
         t("r_len", lang, min=config.PASSWORD_MIN_LENGTH, n=len(p))),
        (any(c.isdigit() for c in p), t("r_digit", lang)),
        (any(c in string.ascii_uppercase for c in p), t("r_upper", lang)),
        (any(c in string.ascii_lowercase for c in p), t("r_lower", lang)),
        (all(c in ALLOWED_CHARS for c in p), t("r_chars", lang)),
        (p.lower() not in COMMON_PASSWORDS, t("r_common", lang)),
        (not name or name.lower() not in p.lower(), t("r_name", lang)),
    ]


def is_strong(password: str, name: str = "") -> bool:
    return all(ok for ok, _ in check_rules(password, name))


def rules_message(password: str, name: str = "", lang: str = "ru") -> str:
    """Понятное сообщение: какие правила выполнены ✅, а какие нет ❌."""
    from i18n import t
    lines = [t("pw_bad", lang)]
    for ok, text in check_rules(password, name, lang):
        lines.append(f"{'✅' if ok else '❌'} {text}")
    lines.append(t("pw_example", lang))
    return "\n".join(lines)


# ---------- Шифрование ----------
# Пароль никогда не хранится в базе открытым текстом.
# Сохраняется только "соль" и хеш — даже админ не увидит сам пароль.

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt.hex() + "$" + h.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$")
    except (ValueError, AttributeError):
        return False
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 100_000)
    return hmac.compare_digest(h.hex(), hash_hex)
