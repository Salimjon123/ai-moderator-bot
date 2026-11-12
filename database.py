"""База данных SQLite: пользователи, файлы (видео/аудио/фото), результаты проверок."""

import json
import sqlite3
from datetime import datetime

from config import DB_PATH


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def init_db():
    conn = _conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id       INTEGER PRIMARY KEY,
            username      TEXT,
            full_name     TEXT,
            name          TEXT,
            phone         TEXT,
            password_hash TEXT,   -- пароль хранится в зашифрованном виде
            is_admin      INTEGER DEFAULT 0,
            registered_at TEXT
        );
        CREATE TABLE IF NOT EXISTS media (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            kind       TEXT,      -- video, video_note, audio, voice, photo, document
            file_id    TEXT,      -- id файла в Telegram (можно переслать снова)
            file_path  TEXT,      -- путь к файлу на диске (если скачался)
            caption    TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS checks (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER,
            kind         TEXT,    -- text, speech, caption
            content      TEXT,
            verdict      TEXT,
            toxicity     REAL,
            danger_words TEXT,
            created_at   TEXT
        );
    """)
    # Если база создана старой версией бота — добавляем колонку для пароля
    columns = [r["name"] for r in conn.execute("PRAGMA table_info(users)")]
    if "password_hash" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    media_columns = [r["name"] for r in conn.execute("PRAGMA table_info(media)")]
    if "transcript" not in media_columns:
        conn.execute("ALTER TABLE media ADD COLUMN transcript TEXT")  # распознанный текст
    conn.commit()
    conn.close()


# ---------- Пользователи ----------
def add_user(user_id, username, full_name, name, phone, password_hash):
    conn = _conn()
    conn.execute(
        """INSERT OR REPLACE INTO users
           (user_id, username, full_name, name, phone, password_hash, is_admin, registered_at)
           VALUES (?, ?, ?, ?, ?, ?,
                   COALESCE((SELECT is_admin FROM users WHERE user_id = ?), 0), ?)""",
        (user_id, username, full_name, name, phone, password_hash, user_id, _now()),
    )
    conn.commit()
    conn.close()


def get_user(user_id):
    conn = _conn()
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def is_registered(user_id) -> bool:
    user = get_user(user_id)
    return user is not None and user["phone"] is not None


def is_admin(user_id) -> bool:
    user = get_user(user_id)
    return user is not None and user["is_admin"] == 1


def set_admin(user_id, value: bool, username=None, full_name=None):
    conn = _conn()
    # Если админ ещё не регистрировался — создаём запись
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, username, full_name, registered_at) "
        "VALUES (?, ?, ?, ?)",
        (user_id, username, full_name, _now()),
    )
    conn.execute("UPDATE users SET is_admin = ? WHERE user_id = ?",
                 (1 if value else 0, user_id))
    conn.commit()
    conn.close()


def all_user_ids():
    conn = _conn()
    rows = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    return [r["user_id"] for r in rows]


def list_users(limit=20):
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM users ORDER BY registered_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows


# ---------- Файлы ----------
def save_media(user_id, kind, file_id, file_path, caption) -> int:
    """Сохраняет файл в базу. Возвращает id записи."""
    conn = _conn()
    cur = conn.execute(
        "INSERT INTO media (user_id, kind, file_id, file_path, caption, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, kind, file_id, file_path, caption, _now()),
    )
    conn.commit()
    media_id = cur.lastrowid
    conn.close()
    return media_id


def set_transcript(media_id, text):
    conn = _conn()
    conn.execute("UPDATE media SET transcript = ? WHERE id = ?", (text, media_id))
    conn.commit()
    conn.close()


def get_media(media_id):
    conn = _conn()
    row = conn.execute("SELECT * FROM media WHERE id = ?", (media_id,)).fetchone()
    conn.close()
    return row


def last_media(kinds: tuple, limit=5):
    conn = _conn()
    marks = ",".join("?" * len(kinds))
    rows = conn.execute(
        f"""SELECT m.*, u.name, u.username FROM media m
            LEFT JOIN users u ON u.user_id = m.user_id
            WHERE m.kind IN ({marks}) ORDER BY m.id DESC LIMIT ?""",
        (*kinds, limit),
    ).fetchall()
    conn.close()
    return rows


# ---------- Проверки ----------
def save_check(user_id, kind, content, result: dict):
    conn = _conn()
    conn.execute(
        "INSERT INTO checks (user_id, kind, content, verdict, toxicity, danger_words, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, kind, content, result.get("verdict"),
         result.get("toxicity_percent"),
         json.dumps(result.get("danger_categories", {}), ensure_ascii=False),
         _now()),
    )
    conn.commit()
    conn.close()


def last_checks(limit=10, only_danger=False):
    conn = _conn()
    where = "WHERE c.verdict = 'Опасно'" if only_danger else ""
    rows = conn.execute(
        f"""SELECT c.*, u.name, u.username FROM checks c
            LEFT JOIN users u ON u.user_id = c.user_id
            {where} ORDER BY c.id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return rows


def stats() -> dict:
    conn = _conn()
    one = lambda q, *a: conn.execute(q, a).fetchone()[0]
    data = {
        "users": one("SELECT COUNT(*) FROM users WHERE phone IS NOT NULL"),
        "checks": one("SELECT COUNT(*) FROM checks"),
        "danger": one("SELECT COUNT(*) FROM checks WHERE verdict = 'Опасно'"),
        "suspicious": one("SELECT COUNT(*) FROM checks WHERE verdict = 'Подозрительно'"),
        "media": {r["kind"]: r["cnt"] for r in conn.execute(
            "SELECT kind, COUNT(*) AS cnt FROM media GROUP BY kind")},
    }
    conn.close()
    return data
