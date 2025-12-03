# auth.py
import sqlite3
import hashlib
import os
from typing import Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")


def init_db():
    """users.db에 users 테이블 생성 (없으면)."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


def _hash_password(password: str) -> str:
    """
    비밀번호를 해시로 변환.
    (MVP 수준: sha256 사용. 실제 상용 서비스에서는 bcrypt/scrypt 권장)
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_user(username: str, password: str) -> Tuple[bool, str]:
    """
    회원가입: username이 중복이면 False, 아니면 True 반환.
    """
    username = username.strip()
    if not username or not password:
        return False, "아이디와 비밀번호를 모두 입력해야 합니다."

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, _hash_password(password)),
        )
        conn.commit()
        return True, "회원가입이 완료되었습니다. 이제 로그인해 주세요."
    except sqlite3.IntegrityError:
        return False, "이미 존재하는 아이디입니다."
    except Exception as e:
        return False, f"회원가입 중 오류가 발생했습니다: {e}"
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Tuple[bool, str]:
    """
    로그인: 아이디/비밀번호가 맞으면 True, 아니면 False.
    """
    username = username.strip()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if not row:
            return False, "존재하지 않는 아이디입니다."

        stored_hash = row[0]
        if stored_hash == _hash_password(password):
            return True, "로그인 성공"
        else:
            return False, "비밀번호가 올바르지 않습니다."
    except Exception as e:
        return False, f"로그인 중 오류가 발생했습니다: {e}"
    finally:
        conn.close()
