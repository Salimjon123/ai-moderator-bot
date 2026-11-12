"""
Распознавание речи из аудио и голосовых (Whisper).

Здесь же исправление совместимости: в библиотеке av версии 16+ убрали
параметр metadata_errors, а faster-whisper его всё ещё передаёт.
Без этой заплатки любое распознавание речи падает с ошибкой.
"""

from functools import lru_cache

import av

_original_open = av.open


def _compatible_open(*args, **kwargs):
    kwargs.pop("metadata_errors", None)
    return _original_open(*args, **kwargs)


av.open = _compatible_open


@lru_cache(maxsize=1)
def _model():
    try:
        # Используем ту же модель, что и video_to_text (не грузим второй раз)
        from video_to_text import _speech_model
        return _speech_model("base")
    except ImportError:
        from faster_whisper import WhisperModel
        return WhisperModel("base", device="cpu", compute_type="int8")


def speech_to_text(path: str) -> str:
    """Аудио/голосовое -> текст."""
    segments, _ = _model().transcribe(path, beam_size=5, vad_filter=False,
                                      condition_on_previous_text=False)
    return " ".join(s.text.strip() for s in segments if s.text.strip())
