"""
Распознавание речи из аудио и голосовых (Whisper).

Здесь же исправление совместимости: в библиотеке av версии 16+ убрали
параметр metadata_errors, а faster-whisper его всё ещё передаёт.
Без этой заплатки любое распознавание речи падает с ошибкой.
"""

from functools import lru_cache

import av

import config

_original_open = av.open


def _compatible_open(*args, **kwargs):
    kwargs.pop("metadata_errors", None)
    return _original_open(*args, **kwargs)


av.open = _compatible_open


@lru_cache(maxsize=1)
def _model():
    try:
        # Та же модель, что и в video_to_text (не грузим её второй раз)
        from video_to_text import _speech_model
        return _speech_model(config.WHISPER_MODEL)
    except ImportError:
        from faster_whisper import WhisperModel
        return WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")


def pick_language(path: str):
    """
    Определяет язык речи, но выбирает ТОЛЬКО из разрешённых (kk, ru, en).
    Без этого Whisper на коротких фразах путал казахский с арабским и др.
    """
    try:
        from faster_whisper.audio import decode_audio
        audio = decode_audio(path)
        _, _, probs = _model().detect_language(audio=audio, language_detection_segments=2)
        allowed = [(lang, p) for lang, p in probs if lang in config.ALLOWED_LANGUAGES]
        return max(allowed, key=lambda x: x[1])[0] if allowed else "ru"
    except Exception:
        return None   # нет звука или ошибка — пусть Whisper решит сам


def transcribe(path: str):
    """Аудио/голосовое -> (текст, язык)."""
    lang = pick_language(path)
    segments, info = _model().transcribe(path, language=lang, beam_size=5,
                                         vad_filter=False,
                                         condition_on_previous_text=False)
    text = " ".join(s.text.strip() for s in segments if s.text.strip())
    return text, (lang or info.language)


def speech_to_text(path: str) -> str:
    """Аудио/голосовое -> текст."""
    return transcribe(path)[0]
