"""
Определение языка текста: казахский, русский или английский.
Остальные языки бот не принимает.

Работает по буквам, без нейросети:
  • есть казахские буквы (ә ғ қ ң ө ұ ү һ і)  -> казахский
  • в основном кириллица                       -> русский
  • в основном латиница                        -> английский
  • арабские, китайские и другие буквы         -> не поддерживается
"""

KAZAKH_LETTERS = set("әғқңөұүһі")
UZBEK_LETTERS = set("ў")          # узбекская кириллица — не поддерживаем
NAMES = {"kk": "қазақ", "ru": "русский", "en": "English"}


def detect_text_language(text: str):
    """Возвращает "kk", "ru", "en" или None (язык не поддерживается / нет букв)."""
    low = text.lower()
    letters = [c for c in low if c.isalpha()]
    if not letters:
        return "ru"   # только цифры, эмодзи или ссылки — проверяем как обычно

    if any(c in UZBEK_LETTERS for c in letters):
        return None

    cyr = sum(1 for c in letters if "\u0400" <= c <= "\u04ff")
    lat = sum(1 for c in letters if "a" <= c <= "z")
    other = len(letters) - cyr - lat

    if other > len(letters) * 0.3:
        return None                     # арабский, китайский и т.п.
    if any(c in KAZAKH_LETTERS for c in letters):
        return "kk"
    return "ru" if cyr >= lat else "en"
