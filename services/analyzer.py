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

from i18n import CATEGORIES, FRAME_NAMES, LABELS, SPEECH_LANGS, VERDICTS, t, tr

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

from services.url_reputation import check_url as vt_check_url

try:
    from antifraud import check_links
except ImportError as e:
    logging.warning(f"antifraud не подключён: {e}")
    check_links = None


def esc(s) -> str:
    """Экранирует текст, чтобы Telegram не сломался на символах < > &."""
    return html.escape(str(s or ""))


VERDICT_EMOJI = {"Безопасно": "🟢", "Подозрительно": "🟡", "Опасно": "🔴"}


def format_report(r: dict, title: str, lang: str = "ru") -> str:
    """Превращает результат check_text в сообщение для Telegram (на языке lang)."""
    verdict = tr(VERDICTS, r["verdict"], lang)
    lines = [
        f"<b>{title}</b>",
        f"{VERDICT_EMOJI.get(r['verdict'], '⚪')} <b>{t('verdict', lang)}: {verdict}</b>",
        f"{t('toxicity', lang)}: <b>{r['toxicity_percent']}%</b>",
    ]
    for key, value in r.get("labels", {}).items():
        if key in LABELS:
            lines.append(f"• {tr(LABELS, key, lang)}: {value}%")
    if r.get("danger_categories"):
        lines.append("\n" + t("found_words", lang))
        for cat, words in r["danger_categories"].items():
            name = tr(CATEGORIES, cat, lang)
            if name == cat:
                name = cat.replace("_", " ").capitalize()
            lines.append(f"• {esc(name)}: {esc(', '.join(words))}")
    return "\n".join(lines)


def format_links(r: dict, lang: str = "ru") -> str:
    """Отчёт antifraud.check_links."""
    if not r.get("urls"):
        return ""
    if r.get("is_phishing"):
        head = t("links_phish", lang)
    elif r.get("is_suspicious"):
        head = t("links_susp", lang)
    else:
        head = t("links_ok", lang)
    lines = [f"{t('links_head', lang)} {head} ({t('risk', lang)} {r.get('score', 0)}%)"]
    for reason in r.get("reasons", [])[:5]:
        lines.append(f"• {esc(reason)}")
    return "\n".join(lines)


def format_vision(r: dict, lang: str = "ru", gemini: bool = False) -> str:
    """Отчёт по кадрам (local_vision или Gemini)."""
    emoji = "🔴" if r.get("is_danger") else "🟢"
    head = t("frames_head_gemini" if gemini else "frames_head", lang)
    lines = [f"{head} {emoji} {t('risk', lang)} {r.get('score', 0)}% "
             f"({t('frames_n', lang, n=r.get('frames_checked', 0))})"]
    if "found" in r:   # локальная проверка — переводим по частям
        for h in r["found"]:
            lines.append("• " + t("frame_hit", lang, name=tr(FRAME_NAMES, h["name"], lang),
                                  n=h["count"], total=r.get("frames_checked", 0), conf=h["conf"]))
        if not r["found"]:
            lines.append("• " + t("frames_clean", lang))
            if r.get("maybe"):
                names = ", ".join(tr(FRAME_NAMES, n, lang) for n in r["maybe"])
                lines.append("• " + t("frames_maybe", lang, names=names))
    else:              # Gemini — причины как есть
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
    lang = db.get_lang(user_id)
    lines = [l for l in text.split("\n") if l.strip()]
    # Несколько строк от пользователя = несколько комментариев
    data = lines if (kind == "text" and len(lines) > 1) else text

    # Модель медленная — запускаем в отдельном потоке, чтобы бот не зависал
    result = await asyncio.to_thread(check_text, data)

    # Ссылки: правила antifraud.py + (если есть ключ) база VirusTotal
    lr = await asyncio.to_thread(check_links, text) if check_links else {}
    for url in lr.get("urls", [])[:3]:
        vt = await asyncio.to_thread(vt_check_url, url)
        if vt is None:
            continue
        if vt["malicious"] >= 2:
            vt_score = 90
        elif vt["malicious"] or vt["suspicious"]:
            vt_score = 60
        else:
            vt_score = 0
        lr["reasons"] = lr.get("reasons", []) + [
            t("vt_bad", lang, url=url, n=vt["malicious"] + vt["suspicious"], total=vt["total"])
            if vt_score else t("vt_clean", lang, url=url)]
        lr["score"] = max(lr.get("score", 0), vt_score)
        lr["is_phishing"] = lr["score"] >= 70
        lr["is_suspicious"] = lr["score"] >= 40

    # Опасная ссылка поднимает общий вердикт: фишинг -> "Опасно", подозрительная -> "Подозрительно"
    if lr.get("is_phishing"):
        result["verdict"] = "Опасно"
    elif lr.get("is_suspicious") and result["verdict"] == "Безопасно":
        result["verdict"] = "Подозрительно"

    db.save_check(user_id, kind, text, result)
    _mark(meta, result["verdict"] == "Опасно", result["verdict"] != "Безопасно")

    report = format_report(result, title, lang)
    links = format_links(lr, lang) if lr else ""
    if links:
        report += "\n\n" + links
    return report


async def analyze_file(user_id: int, path: str, kind: str, meta: dict = None) -> list:
    """Анализ видео, фото и аудио. Возвращает список частей отчёта.
    meta (необязательно) — сюда записывается: danger, suspicious, transcript."""
    lang = db.get_lang(user_id)
    parts = []
    if not path:
        return parts

    # Аудио и голосовые: речь -> текст -> проверка текста
    if kind in ("audio", "voice"):
        if not speech_to_text:
            return [t("speech_missing", lang)]
        try:
            spoken, speech_lang = await asyncio.to_thread(transcribe, path)
            if spoken.strip():
                if meta is not None:
                    meta["transcript"] = spoken
                parts.append(await analyze_text(user_id, spoken, "speech",
                                                t("title_voice", lang), meta))
                parts.append(t("speech_lang", lang, lang=tr(SPEECH_LANGS, speech_lang, lang)))
                # Текст показывается по кнопке "Показать текст" (и для опасного тоже)
                if meta is None:
                    parts.append(f"<i>{t('recognized', lang)}: {esc(spoken[:300])}</i>")
            else:
                parts.append(t("no_speech_audio", lang))
        except Exception as e:
            logging.exception("speech_to_text")
            parts.append(t("speech_error", lang, e=esc(e)))
        return parts

    if kind not in ("video", "video_note", "photo"):
        return parts

    # 1) Кадры: 18+, насилие, оружие (локально, без ключей)
    if check_frames:
        try:
            vis = await asyncio.to_thread(check_frames, path, kind)
            parts.append(format_vision(vis, lang))
            _mark(meta, vis["is_danger"])
            db.save_check(user_id, "frames", "; ".join(vis["reasons"]), {
                "verdict": "Опасно" if vis["is_danger"] else "Безопасно",
                "toxicity_percent": vis["score"], "danger_categories": {}})
        except Exception as e:
            logging.exception("local_vision")
            parts.append(t("frames_error", lang, e=esc(e)))

    # 2) Дополнительно Gemini — только если задан ключ
    if vision_check and os.getenv("GEMINI_API_KEY") and kind != "photo":
        try:
            vis = await asyncio.to_thread(vision_check, path)
            parts.append(format_vision(vis, lang, gemini=True))
            _mark(meta, vis.get("is_danger", False))
        except Exception as e:
            logging.exception("vision_check")
            parts.append("Gemini: " + t("frames_error", lang, e=esc(e)))

    # 3) Речь + надписи на экране -> текст -> проверка текста
    if video_to_text and kind != "photo":
        try:
            # Язык речи выбираем только из казахского, русского, английского
            speech_lang = await asyncio.to_thread(pick_language, path) if pick_language else None
            spoken = await asyncio.to_thread(video_to_text, path,
                                             model_size=config.WHISPER_MODEL, language=speech_lang)
            if speech_lang:
                parts.append(t("speech_lang", lang, lang=tr(SPEECH_LANGS, speech_lang, lang)))
            if spoken and spoken.strip():
                parts.append(await analyze_text(user_id, spoken, "speech",
                                                t("title_speech_video", lang), meta))
                parts.append(f"<i>{t('recognized', lang)}: {esc(spoken[:300])}</i>")
            else:
                parts.append(t("no_speech_video", lang))
        except Exception as e:
            # Например, не скачалась модель EasyOCR — тогда распознаём хотя бы речь
            logging.exception("video_to_text")
            try:
                spoken = await asyncio.to_thread(speech_to_text, path) if speech_to_text else ""
                if spoken.strip():
                    parts.append(await analyze_text(user_id, spoken, "speech",
                                                    t("title_speech_only", lang), meta))
                    parts.append(f"<i>{t('recognized', lang)}: {esc(spoken[:300])}</i>")
                else:
                    parts.append(t("no_speech_video2", lang))
            except Exception as e2:
                logging.exception("speech_to_text")
                parts.append(t("speech_error", lang, e=esc(e2)))
    return parts


async def analyze_link(user_id: int, url: str, meta: dict = None) -> list:
    """Скачивает видео по ссылке (YouTube/TikTok/Instagram) и проверяет всё.
    meta (необязательно) — сюда записывается: danger, media_id, video_path."""
    lang = db.get_lang(user_id)
    if not parse_url:
        return [t("parser_missing", lang)]

    folder = os.path.join(config.MEDIA_DIR, "links")
    warning = ""
    try:
        info = await asyncio.to_thread(parse_url, url, download_video=True,
                                       output_dir=folder, max_comments=10)
    except Exception as e:
        # Видео не скачалось — проверяем хотя бы название, описание и комментарии
        logging.warning(f"Видео не скачано: {e}")
        warning = t("link_dl_warn", lang)
        info = await asyncio.to_thread(parse_url, url, download_video=False,
                                       output_dir=folder, max_comments=10)
    path = info.get("video_path")
    media_id = db.save_media(user_id, "link_video", url, path, info.get("title"))
    if meta is not None:
        meta["media_id"] = media_id
        meta["video_path"] = path

    parts = [f"🎬 <b>{esc(info.get('title') or t('video_word', lang))}</b>\n"
             f"{t('channel', lang)}: {esc(info['metadata'].get('channel') or '—')}"]

    # Название, описание и комментарии
    text = "\n".join(x for x in [info.get("title"), info.get("description")] if x)
    comments = [c.get("text", "") if isinstance(c, dict) else str(c)
                for c in info.get("comments") or []]
    if text.strip():
        parts.append(await analyze_text(user_id, text, "description",
                                        t("title_desc", lang), meta))
    if comments:
        parts.append(await analyze_text(user_id, "\n".join(comments), "text",
                                        t("title_comments", lang, n=len(comments)), meta))

    # Само видео
    if path:
        parts += await analyze_file(user_id, path, "video", meta)
    else:
        parts.append(warning or t("link_dl_warn", lang))
    return parts


def warm_up():
    """Загружает модели заранее, чтобы первая проверка была быстрой."""
    check_text("тест")
    if check_frames:
        from services import local_vision
        local_vision._nsfw()
        local_vision._clip()
