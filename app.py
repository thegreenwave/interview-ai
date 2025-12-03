import os
import random
import difflib
import numpy as np
import librosa
import streamlit as st
from openai import OpenAI
import plotly.graph_objects as go
import plotly.express as px
import pdfplumber  # PyPDF2 대신 더 강력한 pdfplumber 사용
from collections import Counter
import json

# ==========================================
# 🔑 기본 설정
# ==========================================
st.set_page_config(page_title="Spec-trum Pro", page_icon="🎙️", layout="wide")

# 1. 접속 비밀번호 설정
password = st.text_input("🔒 접속 비밀번호를 입력하세요", type="password")
if password != "0601":
    st.warning("비밀번호가 틀렸습니다.")
    st.stop()

# 2. API 키 설정 (Streamlit Secrets에서 가져오기)
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
else:
    # 로컬 테스트용
    pass

client = OpenAI()

# ==========================================
# 📊 분석 함수 모음 (엔진)
# ==========================================
def analyze_audio_features(y, sr):
    """오디오의 물리적 특징 추출 (속도, 침묵, 톤, 크기 등)"""
    rms = librosa.feature.rms(y=y)[0]
    times = librosa.times_like(rms, sr=sr)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    
    # 침묵 구간 계산 (25dB 기준)
    non_silent_intervals = librosa.effects.split(y, top_db=25)
    non_silent_duration = sum([(end - start) for start, end in non_silent_intervals]) / sr
    total_duration = librosa.get_duration(y=y, sr=sr)
    
    # 첫 발화까지 걸린 시간 (Initial Delay)
    if len(non_silent_intervals) > 0:
        initial_silence = librosa.frames_to_time(non_silent_intervals[0][0], sr=sr)
    else:
        initial_silence = 0
    
    silence_duration = total_duration - non_silent_duration
    silence_ratio = silence_duration / total_duration if total_duration > 0 else 0
    
    return times, rms, cent, total_duration, non_silent_duration, silence_duration, silence_ratio, initial_silence

def analyze_text_patterns(text):
    """텍스트에서 습관어(Filler)와 핵심 키워드 분석"""
    fillers = ["음", "어", "그", "막", "이제", "약간", "저", "사실"]
    filler_counts = {f: text.count(f) for f in fillers if text.count(f) > 0}
    total_fillers = sum(filler_counts.values())
    
    words = text.replace(".", "").split()
    valid_words = [w for w in words if len(w) >= 2 and w not in fillers]
    top_keywords = Counter(valid_words).most_common(5)
    
    return filler_counts, total_fillers, top_keywords

def extract_text_from_pdf(pdf_file):
    """pdfplumber를 사용한 텍스트 추출 (배포 환경 호환성 우수)"""
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        # 페이지 제한 없이 전체 읽기
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text

def calculate_similarity(text1, text2):
    """대본 일치도 계산"""
    matcher = difflib.SequenceMatcher(None, text1, text2)
    return matcher.ratio() * 100

# ==========================================
# 🎛️ 메인 UI & 사이드바
# ==========================================
with st.sidebar:
    st.title("SPEC-TRUM")
    st.caption("역량 전달의 스펙트럼을 넓히다")
    st.markdown("---")
    menu = st.radio("기능 선택", ["1. 발표 준비", "2. 생기부 심층 면접"])
    st.markdown("---")

# ==========================================
# [기능 1] 발표 준비
# ==========================================
if menu == "1. 발표 준비":
    st.title("🎤 발표 준비")
    
    tab1, tab2, tab3 = st.tabs(["📝 1.1 대본 작성", "🧐 1.2 대본 평가", "📊 1.3 발표 능력 평가"])
    
    # --- [1.1 대본 작성] ---
    with tab1:
        st.header("AI가 발표 대본을 작성해 드립니다.")
        col1, col2 = st.columns(2)
        with col1:
            p_
