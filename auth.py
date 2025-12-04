# auth.py
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    
    # 1. 사용자 테이블 (비밀번호는 해시 처리하여 저장)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. 문의 내역 테이블
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

def create_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    
    # 비밀번호 해싱
    hashed_pw = make_hashes(password)
    
    try:
        c.execute('INSERT INTO users(username, password) VALUES (?,?)', (username, hashed_pw))
        conn.commit()
        return True, "회원가입이 완료되었습니다. 로그인해주세요."
    except sqlite3.IntegrityError:
        return False, "이미 존재하는 아이디입니다."
    except Exception as e:
        return False, f"오류 발생: {e}"
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()
    
    if data:
        # DB에 저장된 해시 비밀번호와 입력된 비밀번호의 해시값 비교
        if check_hashes(password, data[0]):
            return True, "로그인 성공"
        else:
            return False, "비밀번호가 일치하지 않습니다."
    else:
        return False, "존재하지 않는 아이디입니다."

def get_all_users_df():
    """관리자용: 모든 사용자 정보를 데이터프레임으로 반환"""
    conn = sqlite3.connect("users.db")
    try:
        # 비밀번호 제외하고 조회
        df = pd.read_sql_query("SELECT username, created_at FROM users", conn)
        
        # 가상의 데이터(가입일, 플랜)를 시각적으로 보여주기 위해 추가 (Demo용)
        import random
        from datetime import datetime, timedelta
        
        # 데모용 랜덤 데이터 생성
        df['join_date'] = pd.to_datetime(df['created_at'])
        df['plan'] = [random.choice(['Free', 'Pro']) for _ in range(len(df))]
        df['last_login'] = [datetime.now() - timedelta(hours=random.randint(0, 72)) for _ in range(len(df))]
    except:
        df = pd.DataFrame(columns=["username", "plan", "join_date"])
    finally:
        conn.close()
    return df

def submit_inquiry(username, category, content):
    """문의 사항 저장"""
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

def get_all_inquiries():
    """관리자용: 모든 문의 내역 불러오기"""
    conn = sqlite3.connect("users.db")
    try:
        df = pd.read_sql_query("SELECT * FROM inquiries ORDER BY created_at DESC", conn)
    except:
        df = pd.DataFrame(columns=["id", "username", "category", "content", "status", "created_at"])
    finally:
        conn.close()
    return df

def check_user_has_inquiry(username):
    """특정 사용자가 이미 문의를 등록했는지 확인 (True면 이미 등록됨)"""
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        c.execute("SELECT 1 FROM inquiries WHERE username = ? LIMIT 1", (username,))
        result = c.fetchone()
        return result is not None
    except:
        return False
    finally:
        conn.close()
