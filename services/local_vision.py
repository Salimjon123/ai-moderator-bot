"""
Локальная проверка кадров (без API-ключей, работает на компьютере).

  • 18+ контент  -> модель Falconsai/nsfw_image_detection
  • драка, оружие, кровь, наркотики -> модель CLIP

Как CLIP решает: он сравнивает кадр со списком описаний и выбирает самое похожее.
Поэтому в списке много ОБЫЧНЫХ сцен — иначе обычный кадр "притягивается" к опасному.
Кадр опасный, только если опасное описание победило с уверенностью выше порога.
Видео опасное, только если таких кадров минимум 2 (одна ошибка модели не считается).
"""

from functools import lru_cache

from PIL import Image

NSFW_MODEL = "Falconsai/nsfw_image_detection"
CLIP_MODEL = "openai/clip-vit-base-patch32"

# (описание для CLIP, название для отчёта или None для обычной сцены)
CLIP_LABELS = [
    # --- опасное ---
    ("a photo of people fighting, punching or kicking each other", "Драка / избиение"),
    ("a photo of a person holding a gun, pistol or rifle", "Оружие"),
    ("a photo of a person threatening someone with a knife", "Оружие (нож)"),
    ("a photo of bloody wounds and injuries", "Кровь / насилие"),
    ("a photo of illegal drugs, white powder or syringes", "Наркотики"),
    # --- обычное ---
    ("a photo of a person sitting at a desk or table", None),
    ("a photo of a person sleeping or resting", None),
    ("a photo of students in a classroom or office", None),
    ("a photo of people talking or hanging out", None),
    ("a photo of a person walking or standing", None),
    ("a selfie or a person looking at the camera", None),
    ("a photo of a room, furniture or interior", None),
    ("a photo of a street, city, nature or landscape", None),
    ("a photo of food or drinks", None),
    ("a photo of people playing sports or dancing", None),
    ("a photo of a phone or computer screen with text", None),
    ("a cartoon, game or animated picture", None),
]

NSFW_THRESHOLD = 0.85   # уверенность модели 18+
CLIP_THRESHOLD = 0.55   # уверенность CLIP для опасной сцены
MIN_BAD_FRAMES = 2      # сколько опасных кадров нужно для вердикта по видео


@lru_cache(maxsize=1)
def _nsfw():
    from transformers import pipeline
    return pipeline("image-classification", model=NSFW_MODEL)


@lru_cache(maxsize=1)
def _clip():
    from transformers import pipeline
    return pipeline("zero-shot-image-classification", model=CLIP_MODEL)


def _frames(path: str, kind: str) -> list:
    if kind == "photo":
        return [Image.open(path).convert("RGB")]
    from vision_check import extract_frames   # модуль Участника 4
    return extract_frames(path, num_frames=10)


def check_frames(path: str, kind: str = "video") -> dict:
    """Проверяет кадры. Возвращает {score, is_danger, reasons, frames_checked}."""
    frames = _frames(path, kind)
    if not frames:
        raise ValueError("Не удалось получить кадры")

    descriptions = [d for d, _ in CLIP_LABELS]
    names = dict(CLIP_LABELS)
    hits = {}   # причина -> список уверенностей по кадрам

    for img in frames:
        # 1) 18+
        for r in _nsfw()(img):
            if r["label"].lower() == "nsfw" and r["score"] >= NSFW_THRESHOLD:
                hits.setdefault("Контент 18+", []).append(r["score"])

        # 2) насилие / оружие / кровь / наркотики
        best = _clip()(img, candidate_labels=descriptions)[0]
        name = names[best["label"]]
        if name and best["score"] >= CLIP_THRESHOLD:
            hits.setdefault(name, []).append(best["score"])

    need = 1 if len(frames) == 1 else MIN_BAD_FRAMES
    found = {n: s for n, s in hits.items() if len(s) >= need}
    maybe = {n: s for n, s in hits.items() if n not in found}

    reasons = [f"{n}: {len(s)} из {len(frames)} кадров (уверенность до {round(max(s) * 100)}%)"
               for n, s in sorted(found.items(), key=lambda x: -max(x[1]))]
    if not reasons:
        reasons = ["Опасного на кадрах не найдено"]
        if maybe:
            reasons.append("Был 1 сомнительный кадр (" + ", ".join(maybe) +
                           ") — скорее всего ошибка модели")
    score = max((max(s) for s in found.values()), default=0.0)
    return {
        "score": round(score * 100, 1),
        "is_danger": bool(found),
        "reasons": reasons,
        "frames_checked": len(frames),
    }
