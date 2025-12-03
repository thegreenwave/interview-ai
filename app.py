import os
import random
import io
import json
import numpy as np
import librosa
import streamlit as st
from openai import OpenAI
import plotly.graph_objects as go



if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

client = OpenAI()


#Logic

st.set_page_config(page_title="Spec-trum: 엔지니어를 위한 기술 면접 코치", page_icon="🧠", layout="wide")

password = st.text_input(" 접속 비밀번호를 입력하세요", type="password")

if password != "0601": 
    st.warning("비밀번호가 틀렸습니다. 접속할 수 없습니다.")
    st.stop()  

# CSS 스타일
st.markdown("""
<style>
.main-title {font-size: 2.1rem; font-weight: 700; color: #1f3b57;}
.question-card {background-color: #ffffff; border-radius: 16px; padding: 1.6rem; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #e0e0e0; margin-bottom: 20px;}
.question-text {font-size: 1.3rem; font-weight: 600; color: #333;}
</style>
""", unsafe_allow_html=True)

# 질문 DB
QUESTION_BANK = {
    "반도체": ["MOSFET의 동작 원리를 설명하시오.", "반도체 8대 공정을 나열하고 식각 공정을 설명하시오.", "SRAM과 DRAM의 차이를 설명하시오."],
    "회로설계": ["Op-Amp의 이상적인 특성과 실제 특성 차이를 설명하시오.", "피드백 회로의 장점을 설명하시오."],
    "SW개발": ["프로세스와 스레드의 차이를 설명하시오.", "REST API의 특징을 설명하시오."]
}

# 사이드바
with st.sidebar:
    st.header("면접 설정")
    job = st.selectbox("지원 직무", ["반도체", "회로설계", "SW개발"])

# 메인 화면
st.markdown('<div class="main-title">Spec-trum: 기술 면접 코치</div>', unsafe_allow_html=True)
st.info(f"선택한 직무: {job}")

if "q" not in st.session_state:
    st.session_state.q = random.choice(QUESTION_BANK[job])

if st.button("🔄 새 질문 받기"):
    st.session_state.q = random.choice(QUESTION_BANK[job])

st.markdown(f'<div class="question-card"><div class="question-text">Q. {st.session_state.q}</div></div>', unsafe_allow_html=True)

# 오디오 입력
audio_input = st.audio_input("🎙 답변 녹음하기")

if audio_input:
    st.success("녹음 완료! 분석 중...")
    
    # 1. Librosa 분석
    y, sr = librosa.load(audio_input, sr=None)
    duration = librosa.get_duration(y=y, sr=sr)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    
    col1, col2 = st.columns(2)
    col1.metric("답변 시간", f"{duration:.1f}초")
    
    # 🚨 [수정된 부분] tempo가 배열로 나올 경우를 대비해 float()로 감싸줍니다.
    col2.metric("말하기 속도", f"{float(tempo):.0f} BPM")
    
    # 2. STT (Whisper)
    audio_input.seek(0)
    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_input).text
    st.markdown("### 🗣 내 답변 (STT)")
    st.write(transcript)
    
    # 3. GPT-4o 평가
    with st.spinner("AI 면접관이 평가 중입니다..."):
        prompt = f"""
        당신은 15년차 면접관이다. 
        질문: {st.session_state.q}
        답변: {transcript}
        
        위 답변을 평가해라.
        1. 필수 키워드 사용 여부
        2. 논리적 구조 (두괄식 여부)
        3. 100점 만점 점수
        4. 개선할 점
        """
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        st.markdown("### 🧑‍💼 AI 면접관 피드백")
        st.write(res.choices[0].message.content)
