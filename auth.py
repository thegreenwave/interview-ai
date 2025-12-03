# auth.py
import sqlite3
import hashlib
import os
from typing import Tuple
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

def get_all_users_df():
    """관리자용: 모든 사용자 정보를 데이터프레임으로 반환"""
    conn = sqlite3.connect("users.db")
    # 비밀번호는 보안상 제외하고 가져옵니다.
    # 만약 테이블 컬럼이 username, password 뿐이라면 아래와 같이 씁니다.
    # created_at 등의 컬럼이 없다면 username만 가져옵니다.
    try:
        df = pd.read_sql_query("SELECT username FROM users", conn)
        # 가상의 데이터(가입일, 플랜)를 시각적으로 보여주기 위해 추가 (실제 컬럼이 있다면 SQL을 수정하세요)
        import random
        from datetime import datetime, timedelta
        
        # 데모용 가짜 데이터 생성
        df['join_date'] = [datetime.now() - timedelta(days=random.randint(0, 365)) for _ in range(len(df))]
        df['plan'] = [random.choice(['Free', 'Pro', 'Free']) for _ in range(len(df))]
        df['last_login'] = [datetime.now() - timedelta(hours=random.randint(0, 72)) for _ in range(len(df))]
    except:
        df = pd.DataFrame(columns=["username", "plan", "join_date"])
    finally:
        conn.close()
    return df


def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    
    # 1. 사용자 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. 문의 내역 테이블 추가
    c.execute('''
        CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            category TEXT,
            content TEXT,
            status TEXT DEFAULT 'Unread',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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

# [NEW] 문의 사항 저장 함수
def submit_inquiry(username, category, content):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO inquiries (username, category, content) VALUES (?, ?, ?)", 
                  (username, category, content))
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()

# [NEW] 관리자용: 모든 문의 내역 불러오기
def get_all_inquiries():
    conn = sqlite3.connect("users.db")
    try:
        df = pd.read_sql_query("SELECT * FROM inquiries ORDER BY created_at DESC", conn)
    except:
        df = pd.DataFrame(columns=["id", "username", "category", "content", "status", "created_at"])
    finally:
        conn.close()
    return df


