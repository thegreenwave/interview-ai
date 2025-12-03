import os
import random
import difflib
import numpy as np
import librosa
import streamlit as st
from openai import OpenAI
import plotly.graph_objects as go
import plotly.express as px
import PyPDF2
from collections import Counter
import json

# ==========================================
# 🔑 기본 설정
# ==========================================
st.set_page_config(page_title="Spec-trum Pro", page_icon="🎓", layout="wide")

password = st.text_input("🔒 접속 비밀번호", type="password")
if password != "0601": # 비밀번호 설정
    st.warning("비밀번호를 입력하세요.")
    st.stop()

if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
else:
    pass

client = OpenAI()

# ==========================================
# 📊 분석 함수 모음
# ==========================================
def analyze_audio_features(y, sr):
    rms = librosa.feature.rms(y=y)[0]
    times = librosa.times_like(rms, sr=sr)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    
    # 침묵 구간 계산 (25dB 기준)
    non_silent_intervals = librosa.effects.split(y, top_db=25)
    non_silent_duration = sum([(end - start) for start, end in non_silent_intervals]) / sr
    total_duration = librosa.get_duration(y=y, sr=sr)
    
    # 첫 발화까지 걸린 시간 (Initial Delay) - 면접에서 중요!
    if len(non_silent_intervals) > 0:
        initial_silence = librosa.frames_to_time(non_silent_intervals[0][0], sr=sr)
    else:
        initial_silence = 0
    
    silence_duration = total_duration - non_silent_duration
    silence_ratio = silence_duration / total_duration if total_duration > 0 else 0
    
    return times, rms, cent, total_duration, non_silent_duration, silence_duration, silence_ratio, initial_silence

def analyze_text_patterns(text):
    fillers = ["음", "어", "그", "막", "이제", "약간", "저"]
    filler_counts = {f: text.count(f) for f in fillers if text.count(f) > 0}
    total_fillers = sum(filler_counts.values())
    return filler_counts, total_fillers

def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages[:5]: 
        text += page.extract_text()
    return text

# ==========================================
# 🎛️ 메인 화면 구성
# ==========================================
with st.sidebar:
    st.title("SPEC-TRUM")
    st.caption("역량의 스펙트럼을 넓히다")
    menu = st.radio("Mode", ["1. 발표 마스터 (All-in-One)", "2. 생기부 심층 면접"])

# ==========================================
# [기능 1] 발표 마스터 (기존 유지 - 요약됨)
# ==========================================
if menu == "1. 발표 마스터 (All-in-One)":
    st.title("🎤 수행평가 발표 마스터")
    tab1, tab2 = st.tabs(["📝 대본 작성", "📊 발표 연습"])
    
    with tab1:
        st.write("발표 주제를 입력하면 대본을 써줍니다.")
        topic = st.text_input("주제")
        if st.button("대본 생성"):
            res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user", "content":f"{topic} 발표 대본 3분 분량 써줘"}])
            st.session_state['script'] = res.choices[0].message.content
            st.success("완료!")
        if 'script' in st.session_state:
            st.text_area("대본", st.session_state['script'])
            
    with tab2:
        st.write("대본을 보고 연습하세요.")
        st.audio_input("발표 녹음 (기능 1은 이전 코드와 동일하므로 생략)")

# ==========================================
# [기능 2] 생기부 심층 면접 (대규모 업데이트)
# ==========================================
elif menu == "2. 생기부 심층 면접":
    st.title("🎓 생활기록부 기반 면접 (입학사정관 모드)")
    st.markdown("생기부 PDF를 분석하여 **나만을 위한 송곳 질문**을 던지고, 답변 태도와 내용을 분석합니다.")
    
    # 2.1 파일 업로드 및 질문 생성
    with st.expander("📂 1단계: 생기부 업로드 및 질문 생성", expanded=True):
        uploaded_file = st.file_uploader("생활기록부 PDF 업로드", type="pdf")
        
        if uploaded_file:
            text = extract_text_from_pdf(uploaded_file)
            if len(text) > 50:
                st.success("생기부 분석 완료!")
                if st.button("🤖 맞춤형 질문 추출하기"):
                    with st.spinner("입학사정관이 생기부를 검토 중입니다..."):
                        prompt = f"""
                        당신은 입학사정관입니다.
                        [생기부 내용]
                        {text[:3000]}
                        
                        지원자의 전공 적합성과 인성을 검증할 수 있는 날카로운 면접 질문 3가지를 만들어주세요.
                        출력 형식:
                        1. [활동명] 질문 내용
                        2. [활동명] 질문 내용
                        3. [활동명] 질문 내용
                        """
                        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                        st.session_state['uni_questions'] = res.choices[0].message.content
            else:
                st.error("텍스트를 읽을 수 없습니다.")

    # 2.2 질문 확인 및 선택
    if 'uni_questions' in st.session_state:
        st.info(st.session_state['uni_questions'])
        target_q = st.text_input("연습할 질문을 여기에 복사해 넣으세요", placeholder="위 질문 중 하나를 골라 입력하세요.")

        st.markdown("---")
        st.subheader("🎙️ 2단계: 실전 답변 & 정밀 분석")
        st.caption("면접관의 눈을 보고 말하듯이 녹음하세요.")
        
        audio_input = st.audio_input("🔴 답변 녹음 시작")
        
        if audio_input and target_q:
            with st.spinner("면접관이 답변을 분석 중입니다..."):
                # 1. 오디오 분석
                y, sr = librosa.load(audio_input, sr=None)
                times, rms, cent, total_dur, _, silent_dur, silence_ratio, initial_silence = analyze_audio_features(y, sr)
                
                tempo_arr, _ = librosa.beat.beat_track(y=y, sr=sr)
                tempo = float(tempo_arr)
                
                # 2. STT 및 텍스트 분석
                audio_input.seek(0)
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_input).text
                filler_counts, total_fillers = analyze_text_patterns(transcript)
                
                # 3. GPT-4o 심층 평가 (JSON 출력 요청)
                eval_prompt = f"""
                역할: 냉철한 입학사정관
                질문: {target_q}
                답변: {transcript}
                
                다음 4가지 항목을 10점 만점으로 평가하고 피드백을 JSON으로 주세요.
                키값: logic(논리성), sincerity(진정성/구체성), confidence(확신/태도), suitability(전공적합성)
                그리고 종합 피드백(feedback)도 포함하세요.
                
                JSON 형식 예시:
                {{
                    "logic": 8,
                    "sincerity": 7,
                    "confidence": 6,
                    "suitability": 9,
                    "feedback": "구체적인 사례는 좋으나..."
                }}
                """
                res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": eval_prompt}],
                    response_format={"type": "json_object"} # JSON 모드 강제
                )
                eval_data = json.loads(res.choices[0].message.content)
                
                # === 📊 결과 리포트 ===
                st.markdown("---")
                
                # [섹션 1] 면접 핵심 지표 (면접 특화)
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("말하기 속도", f"{tempo:.0f} BPM", help="110~130 BPM이 가장 신뢰감을 줍니다.")
                m2.metric("첫마디 반응 속도", f"{initial_silence:.1f}초", delta="빠를수록 좋음", delta_color="inverse", help="질문 후 답변 시작까지 걸린 시간입니다.")
                m3.metric("습관어(음/어)", f"{total_fillers}회", delta="0회가 목표", delta_color="inverse")
                m4.metric("답변 길이", f"{total_dur:.1f}초", help="40~60초가 적당합니다.")

                st.markdown("---")
                
                # [섹션 2] 시각적 분석 (레이더 차트 & 파이 차트)
                g1, g2 = st.columns(2)
                
                with g1:
                    st.subheader("🕸️ 역량 평가 레이더")
                    categories = ['논리성', '진정성(구체성)', '자신감(태도)', '전공적합성']
                    scores = [eval_data['logic']*10, eval_data['sincerity']*10, eval_data['confidence']*10, eval_data['suitability']*10]
                    
                    fig = go.Figure(data=go.Scatterpolar(
                        r=scores, theta=categories, fill='toself', line_color='#4F46E5'
                    ))
                    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=300)
                    st.plotly_chart(fig, use_container_width=True)
                    
                with g2:
                    st.subheader("⏱️ 발화 점유율")
                    fig_pie = px.pie(values=[total_dur - silent_dur, silent_dur], names=["답변(말)", "침묵(생각)"], 
                                     color_discrete_sequence=['#4F46E5', '#E0E7FF'], hole=0.4)
                    fig_pie.update_layout(height=300)
                    st.plotly_chart(fig_pie, use_container_width=True)
                    if initial_silence > 3.0:
                        st.warning(f"⚠️ 답변 시작까지 {initial_silence:.1f}초나 걸렸습니다. 망설이는 인상을 줄 수 있어요.")

                # [섹션 3] 상세 피드백
                st.subheader("🧑‍💼 입학사정관 총평")
                st.info(eval_data['feedback'])
                
                with st.expander("🗣️ 내 답변 텍스트 보기"):
                    st.write(transcript)
                    if filler_counts:
                        st.write("🔴 감지된 습관어:", filler_counts)
