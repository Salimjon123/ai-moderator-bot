"""
Анализ контента: вызывает модули команды и делает красивый отчёт.

  text_check.py    (Участник 2) -> check_text(text)
  video_to_text.py (Участник 3) -> video_to_text(path) -> str
  vision_check.py  (Участник 4) -> check_video_safety(path) -> dict (нужен GEMINI_API_KEY)
  antifraud.py     (Участник 5) -> check_links(text) -> dict
Если какого-то файла нет — этот модуль просто пропускается.
"""

import asyncio
import html
import logging
import os

import config
import database as db
from text_check import check_text

# Ключ Gemini для vision_check (берётся из config.py или переменной окружения)
if config.GEMINI_API_KEY:
    os.environ.setdefault("GEMINI_API_KEY", config.GEMINI_API_KEY)

# ---------- Модули коллег ----------
try:
    from services.speech import pick_language, speech_to_text, transcribe  # + исправление av
except ImportError as e:
    logging.warning(f"speech не подключён: {e}")
    speech_to_text = transcribe = pick_language = None

from services.language import NAMES as LANG_NAMES

try:
    from video_to_text import video_to_text
except ImportError as e:
    logging.warning(f"video_to_text не подключён: {e}")
    video_to_text = None

try:
    from vision_check import check_video_safety as vision_check
except ImportError as e:
    logging.warning(f"vision_check не подключён: {e}")
    vision_check = None

try:
    from services.local_vision import check_frames
except ImportError as e:
    logging.warning(f"local_vision не подключён: {e}")
    check_frames = None

try:
    from parser import parse_url   # модуль Участника 1 (скачивание по ссылке)
except ImportError as e:
    logging.warning(f"parser не подключён: {e}")
    parse_url = None

try:
    from antifraud import check_links
except ImportError as e:
    logging.warning(f"antifraud не подключён: {e}")
    check_links = None


def esc(s) -> str:
    """Экранирует текст, чтобы Telegram не сломался на символах < > &."""
    return html.escape(str(s or ""))


VERDICT_EMOJI = {"Безопасно": "🟢", "Подозрительно": "🟡", "Опасно": "🔴"}
LABEL_NAMES = {"insult": "Оскорбления", "obscenity": "Мат",
               "threat": "Угрозы", "dangerous": "Опасный контент"}


def format_report(r: dict, title: str) -> str:
    """Превращает результат check_text в сообщение для Telegram."""
    lines = [
        f"<b>{title}</b>",
        f"{VERDICT_EMOJI.get(r['verdict'], '⚪')} <b>Вердикт: {r['verdict']}</b>",
        f"Токсичность: <b>{r['toxicity_percent']}%</b>",
    ]
    for key, value in r.get("labels", {}).items():
        if key in LABEL_NAMES:
            lines.append(f"• {LABEL_NAMES[key]}: {value}%")
    if r.get("danger_categories"):
        lines.append("\n⚠️ <b>Найдены опасные слова:</b>")
        for cat, words in r["danger_categories"].items():
            lines.append(f"• {esc(cat.replace('_', ' ').capitalize())}: "
                         f"{esc(', '.join(words))}")
    return "\n".join(lines)


def format_links(r: dict) -> str:
    """Отчёт antifraud.check_links."""
    if not r.get("urls"):
        return ""
    if r.get("is_phishing"):
        head = "🔴 Похоже на фишинг"
    elif r.get("is_suspicious"):
        head = "🟡 Подозрительные ссылки"
    else:
        head = "🟢 Ссылки выглядят нормально"
    lines = [f"🔗 <b>Проверка ссылок:</b> {head} (риск {r.get('score', 0)}%)"]
    for reason in r.get("reasons", [])[:5]:
        lines.append(f"• {esc(reason)}")
    return "\n".join(lines)


def format_vision(r: dict) -> str:
    """Отчёт vision_check.check_video_safety."""
    emoji = "🔴" if r.get("is_danger") else "🟢"
    lines = [f"👁 <b>Анализ кадров:</b> {emoji} риск {r.get('score', 0)}% "
             f"(кадров: {r.get('frames_checked', 0)})"]
    for reason in r.get("reasons", [])[:5]:
        lines.append(f"• {esc(reason)}")
    return "\n".join(lines)


def _mark(meta, danger: bool, suspicious: bool = False):
    """Запоминает в meta, нашлось ли опасное (нужно для кнопок под ответом)."""
    if meta is not None:
        meta["danger"] = meta.get("danger", False) or danger
        meta["suspicious"] = meta.get("suspicious", False) or suspicious or danger


async def analyze_text(user_id: int, text: str, kind: str, title: str,
                       meta: dict = None) -> str:
    """Проверяет текст, сохраняет результат в базу, возвращает отчёт."""
    lines = [l for l in text.split("\n") if l.strip()]
    # Несколько строк от пользователя = несколько комментариев
    data = lines if (kind == "text" and len(lines) > 1) else text

    # Модель медленная — запускаем в отдельном потоке, чтобы бот не зависал
    result = await asyncio.to_thread(check_text, data)
    db.save_check(user_id, kind, text, result)
    _mark(meta, result["verdict"] == "Опасно", result["verdict"] != "Безопасно")

    report = format_report(result, title)
    if check_links:
        lr = await asyncio.to_thread(check_links, text)
        links = format_links(lr)
        if links:
            report += "\n\n" + links
            _mark(meta, lr.get("is_phishing", False), lr.get("is_suspicious", False))
    return report


async def analyze_file(user_id: int, path: str, kind: str, meta: dict = None) -> list:
    """Анализ видео, фото и аудио. Возвращает список частей отчёта.
    meta (необязательно) — сюда записывается: danger, suspicious, transcript."""
    parts = []
    if not path:
        return parts

    # Аудио и голосовые: речь -> текст -> проверка текста
    if kind in ("audio", "voice"):
        if not speech_to_text:
            return ["🎙 Распознавание речи не подключено."]
        try:
            spoken, lang = await asyncio.to_thread(transcribe, path)
            if spoken.strip():
                if meta is not None:
                    meta["transcript"] = spoken
                parts.append(await analyze_text(user_id, spoken, "speech",
                                                "🎙 Анализ голоса", meta))
                parts.append(f"🌐 Язык речи: {LANG_NAMES.get(lang, lang)}")
                # Опасное показываем сразу как доказательство,
                # безопасное — по кнопке "Показать текст"
                if meta is None or meta.get("suspicious"):
                    parts.append(f"<i>Распознано: {esc(spoken[:300])}</i>")
            else:
                parts.append("🎙 Речь в аудио не найдена.")
        except Exception as e:
            logging.exception("speech_to_text")
            parts.append(f"🎙 Не удалось распознать речь: {esc(e)}")
        return parts

    if kind not in ("video", "video_note", "photo"):
        return parts

    # 1) Кадры: 18+, насилие, оружие (локально, без ключей)
    if check_frames:
        try:
            vis = await asyncio.to_thread(check_frames, path, kind)
            parts.append(format_vision(vis))
            _mark(meta, vis["is_danger"])
            db.save_check(user_id, "frames", "; ".join(vis["reasons"]), {
                "verdict": "Опасно" if vis["is_danger"] else "Безопасно",
                "toxicity_percent": vis["score"], "danger_categories": {}})
        except Exception as e:
            logging.exception("local_vision")
            parts.append(f"👁 Не удалось проверить кадры: {esc(e)}")

    # 2) Дополнительно Gemini — только если задан ключ
    if vision_check and os.getenv("GEMINI_API_KEY") and kind != "photo":
        try:
            vis = await asyncio.to_thread(vision_check, path)
            parts.append(format_vision(vis).replace("Анализ кадров", "Анализ кадров (Gemini)"))
            _mark(meta, vis.get("is_danger", False))
        except Exception as e:
            logging.exception("vision_check")
            parts.append(f"👁 Gemini: не удалось проверить кадры: {esc(e)}")

    # 3) Речь + надписи на экране -> текст -> проверка текста
    if video_to_text and kind != "photo":
        try:
            # Язык речи выбираем только из казахского, русского, английского
            lang = await asyncio.to_thread(pick_language, path) if pick_language else None
            spoken = await asyncio.to_thread(video_to_text, path,
                                             model_size=config.WHISPER_MODEL, language=lang)
            if lang:
                parts.append(f"🌐 Язык речи: {LANG_NAMES.get(lang, lang)}")
            if spoken and spoken.strip():
                parts.append(await analyze_text(user_id, spoken, "speech",
                                                "🗣 Анализ речи и надписей", meta))
                parts.append(f"<i>Распознано: {esc(spoken[:300])}</i>")
            else:
                parts.append("🗣 Речи и надписей в видео не найдено.")
        except Exception as e:
            # Например, не скачалась модель EasyOCR — тогда распознаём хотя бы речь
            logging.exception("video_to_text")
            try:
                spoken = await asyncio.to_thread(speech_to_text, path) if speech_to_text else ""
                if spoken.strip():
                    parts.append(await analyze_text(user_id, spoken, "speech",
                                                    "🗣 Анализ речи (без надписей)", meta))
                    parts.append(f"<i>Распознано: {esc(spoken[:300])}</i>")
                else:
                    parts.append("🗣 Речи в видео не найдено.")
            except Exception as e2:
                logging.exception("speech_to_text")
                parts.append(f"🗣 Не удалось распознать речь: {esc(e2)}")
    return parts


async def analyze_link(user_id: int, url: str, meta: dict = None) -> list:
    """Скачивает видео по ссылке (YouTube/TikTok/Instagram) и проверяет всё.
    meta (необязательно) — сюда записывается: danger, media_id, video_path."""
    if not parse_url:
        return ["❌ Модуль parser.py не подключён — ссылки не проверяются."]

    folder = os.path.join(config.MEDIA_DIR, "links")
    warning = ""
    try:
        info = await asyncio.to_thread(parse_url, url, download_video=True,
                                       output_dir=folder, max_comments=10)
    except Exception as e:
        # Видео не скачалось — проверяем хотя бы название, описание и комментарии
        logging.warning(f"Видео не скачано: {e}")
        warning = ("⚠️ Само видео скачать не удалось (YouTube не отдал файл), "
                   "проверены только название, описание и комментарии.\n"
                   "Чтобы видео скачивалось, выполни в терминале: pip install -U deno 'yt-dlp[default]'")
        info = await asyncio.to_thread(parse_url, url, download_video=False,
                                       output_dir=folder, max_comments=10)
    path = info.get("video_path")
    media_id = db.save_media(user_id, "link_video", url, path, info.get("title"))
    if meta is not None:
        meta["media_id"] = media_id
        meta["video_path"] = path

    parts = [f"🎬 <b>{esc(info.get('title') or 'Видео')}</b>\n"
             f"Канал: {esc(info['metadata'].get('channel') or '—')}"]

    # Название, описание и комментарии
    text = "\n".join(x for x in [info.get("title"), info.get("description")] if x)
    comments = [c.get("text", "") if isinstance(c, dict) else str(c)
                for c in info.get("comments") or []]
    if text.strip():
        parts.append(await analyze_text(user_id, text, "description",
                                        "📄 Анализ названия и описания", meta))
    if comments:
        parts.append(await analyze_text(user_id, "\n".join(comments), "text",
                                        f"💬 Анализ комментариев ({len(comments)})", meta))

    # Само видео
    if path:
        parts += await analyze_file(user_id, path, "video", meta)
    else:
        parts.append(warning or "⚠️ Видео не удалось скачать, проверены только текст и описание.")
    return parts


def warm_up():
    """Загружает модели заранее, чтобы первая проверка была быстрой."""
    check_text("тест")
    if check_frames:
        from services import local_vision
        local_vision._nsfw()
        local_vision._clip()
