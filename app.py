import os
import random
import difflib
import numpy as np
import librosa
import streamlit as st
from openai import OpenAI
import plotly.graph_objects as go
import PyPDF2  # PDF 읽기용 라이브러리

# ==========================================
# 🔑 기본 설정 및 비밀번호 잠금
# ==========================================
st.set_page_config(page_title="Spec-trum Uni", page_icon="🎓", layout="wide")

# 1. 앱 접속 비밀번호 (간단 잠금)
password = st.text_input("🔒 접속 비밀번호를 입력하세요", type="password")
if password != "0601": 
    st.warning("비밀번호가 틀렸습니다. 접속할 수 없습니다.")
    st.stop()  # 비밀번호 틀리면 여기서 멈춤

# 2. OpenAI API 키 설정 (Secrets 또는 환경변수)
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
else:
    # 로컬 테스트 등을 위해 필요하다면 여기에 키 직접 입력 (배포 시엔 삭제 권장)
    pass

client = OpenAI()

# ==========================================
# 📊 분석 함수 모음
# ==========================================

def calculate_similarity(text1, text2):
    """두 텍스트 간의 유사도(발음 정확성 지표) 계산"""
    matcher = difflib.SequenceMatcher(None, text1, text2)
    return matcher.ratio() * 100

def analyze_audio_features(y, sr):
    """오디오 특징 추출 (크기, 톤, 침묵 등)"""
    rms = librosa.feature.rms(y=y)[0]
    times = librosa.times_like(rms, sr=sr)
    
    # 톤 높낮이 (Spectral Centroid 활용)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    
    # 침묵 구간 계산
    non_silent_intervals = librosa.effects.split(y, top_db=20)
    non_silent_duration = sum([(end - start) for start, end in non_silent_intervals]) / sr
    total_duration = librosa.get_duration(y=y, sr=sr)
    
    if total_duration > 0:
        silence_ratio = (total_duration - non_silent_duration) / total_duration
    else:
        silence_ratio = 0
        
    return times, rms, cent, total_duration, silence_ratio

def extract_text_from_pdf(pdf_file):
    """PDF 파일에서 텍스트 추출"""
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    # 너무 길면 토큰 제한이 있으므로 앞부분 5페이지만 읽기
    for page in reader.pages[:5]: 
        text += page.extract_text()
    return text

# ==========================================
# 🎛️ 사이드바 메뉴
# ==========================================
with st.sidebar:
    st.title("🎓 Spec-trum Uni")
    st.info("학생들을 위한 발표 & 면접 코치")
    menu = st.radio("기능 선택", ["1. 발표 All-in-One", "2. 생기부 기반 대입 면접"])

# ==========================================
# [기능 1] 발표 All-in-One
# ==========================================
if menu == "1. 발표 All-in-One":
    st.title("🎤 수행평가 발표 마스터")
    
    tab1, tab2, tab3 = st.tabs(["📝 1.1 대본 작성", "🧐 1.2 대본 평가", "📊 1.3 발표 능력 평가"])
    
    # --- [1.1 대본 작성] ---
    with tab1:
        st.header("AI가 발표 대본을 작성해 드립니다.")
        col1, col2 = st.columns(2)
        with col1:
            p_topic = st.text_input("발표 주제", placeholder="예: 생성형 AI의 교육적 활용")
            p_context = st.text_input("발표 상황", placeholder="예: 정보 교과 수행평가")
        with col2:
            p_requirements = st.text_area("요구사항", placeholder="3분 발표, 서론-본론-결론 구조")
            
        if st.button("✨ 대본 생성하기"):
            if not p_topic:
                st.warning("주제를 입력해주세요.")
            else:
                with st.spinner("GPT-4o-mini가 대본을 작성 중입니다..."):
                    prompt = f"주제: {p_topic}\n상황: {p_context}\n요구사항: {p_requirements}\n위 내용을 바탕으로 발표 대본을 작성해줘."
                    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
                    st.session_state['script'] = res.choices[0].message.content
                    st.success("대본 생성 완료!")

        if 'script' in st.session_state:
            st.text_area("생성된 대본", st.session_state['script'], height=300)

    # --- [1.2 대본 평가] ---
    with tab2:
        st.header("작성한 대본 피드백")
        user_script = st.text_area("평가받을 대본 입력", value=st.session_state.get('script', ""), height=200)
        user_intent = st.text_input("의도하고자 하는 바", placeholder="예: 나의 비판적 사고력을 강조")
        
        if st.button("🧐 피드백 받기"):
            if user_script:
                with st.spinner("분석 중..."):
                    prompt = f"대본: {user_script}\n의도: {user_intent}\n이 대본을 평가하고 수정할 점 3가지를 알려줘."
                    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                    st.info(res.choices[0].message.content)

    # --- [1.3 발표 능력 평가] ---
    with tab3:
        st.header("📊 실전 발표 능력 심층 분석")
        ref_text = st.text_area("기준 대본 (발음 정확도 측정용)", value=st.session_state.get('script', ""), height=100)
        audio_input = st.audio_input("🔴 녹음 시작")
        
        if audio_input and ref_text:
            with st.spinner("정밀 분석 중..."):
                # 1. 오디오 분석
                y, sr = librosa.load(audio_input, sr=None)
                times, rms, cent, duration, silence_ratio = analyze_audio_features(y, sr)
                tempo_arr, _ = librosa.beat.beat_track(y=y, sr=sr)
                tempo = float(tempo_arr)
                
                # 2. STT
                audio_input.seek(0)
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_input).text
                
                # 3. 정확도
                accuracy = calculate_similarity(ref_text, transcript)
                
                # 결과 표시
                st.markdown("---")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("속도 (BPM)", f"{tempo:.0f}")
                c2.metric("버벅임 비율", f"{silence_ratio*100:.1f}%")
                c3.metric("발음 정확도", f"{accuracy:.1f}%")
                c4.metric("시간", f"{duration:.1f}초")
                
                # 그래프
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=times, y=rms, name='목소리 크기', fill='tozeroy', line=dict(color='firebrick')))
                norm_cent = (cent - np.min(cent)) / (np.max(cent) - np.min(cent)) * np.max(rms)
                fig.add_trace(go.Scatter(x=times, y=norm_cent, name='톤 높낮이', line=dict(color='royalblue'), opacity=0.5))
                fig.update_layout(title="목소리 변화 분석", height=300)
                st.plotly_chart(fig, use_container_width=True)

# ==========================================
# [기능 2] 생기부 기반 대입 면접
# ==========================================
elif menu == "2. 생기부 기반 대입 면접":
    st.title("🎓 생활기록부 기반 면접 (입학사정관 모드)")
    st.markdown("생기부(PDF)를 업로드하면 AI 입학사정관이 **맞춤형 질문**을 던집니다.")
    
    uploaded_file = st.file_uploader("📂 생활기록부 PDF 업로드", type="pdf")
    
    if uploaded_file is not None:
        with st.spinner("생기부 분석 중..."):
            text = extract_text_from_pdf(uploaded_file)
            if len(text) < 50:
                st.error("텍스트를 읽을 수 없습니다.")
            else:
                st.success("✅ 분석 완료!")
                if st.button("🤖 면접 질문 생성하기"):
                    prompt = f"당신은 입학사정관입니다.\n[생기부 내용]\n{text[:3000]}\n위 내용을 바탕으로 날카로운 면접 질문 3가지를 만들어주세요."
                    res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                    st.session_state['generated_questions'] = res.choices[0].message.content

    if 'generated_questions' in st.session_state:
        st.markdown("---")
        st.info(st.session_state['generated_questions'])
        
        target_q = st.text_input("답변할 질문을 복사해 넣으세요")
        audio_input = st.audio_input("🔴 답변 녹음")
        
        if audio_input and target_q:
            with st.spinner("평가 중..."):
                audio_input.seek(0)
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_input).text
                
                st.write(f"🗣 답변: {transcript}")
                
                eval_prompt = f"질문: {target_q}\n답변: {transcript}\n역할: 입학사정관\n평가: 구체성, 진정성, 논리성 기준으로 점수와 피드백을 주세요."
                res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": eval_prompt}])
                st.write(res.choices[0].message.content)
