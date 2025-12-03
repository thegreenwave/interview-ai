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
# 🔑 설정 및 API 키
# ==========================================
st.set_page_config(page_title="Spec-trum Uni", page_icon="🎓", layout="wide")

password = st.text_input(" 접속 비밀번호를 입력하세요", type="password")

if password != "0601": 
    st.warning("비밀번호가 틀렸습니다. 접속할 수 없습니다.")
    st.stop()  

if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
else:
    pass

client = OpenAI()

# ==========================================
# 📊 공통 분석 함수 (발표/면접 공용)
# ==========================================
def analyze_audio_features(y, sr):
    rms = librosa.feature.rms(y=y)[0]
    times = librosa.times_like(rms, sr=sr)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    non_silent_intervals = librosa.effects.split(y, top_db=20)
    non_silent_duration = sum([(end - start) for start, end in non_silent_intervals]) / sr
    total_duration = librosa.get_duration(y=y, sr=sr)
    silence_ratio = (total_duration - non_silent_duration) / total_duration
    return times, rms, cent, total_duration, silence_ratio

def extract_text_from_pdf(pdf_file):
    """PDF 파일에서 텍스트 추출"""
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    # 너무 길면 비용 문제/토큰 제한이 있으므로 앞부분 5페이지만 읽기 (조절 가능)
    for page in reader.pages[:5]: 
        text += page.extract_text()
    return text

# ==========================================
# 🎛️ 사이드바
# ==========================================
with st.sidebar:
    st.title("🎓 Spec-trum Uni")
    st.info("대입 수시 면접 & 수행평가 발표")
    menu = st.radio("기능 선택", ["1. 수행평가 발표 마스터", "2. 생기부 기반 대입 면접"])

# ==========================================
# [기능 1] 발표 All-in-One (기존 유지)
# ==========================================
if menu == "1. 수행평가 발표 마스터":
    st.title("🎤 수행평가 발표 마스터")
    tab1, tab2, tab3 = st.tabs(["📝 대본 작성", "🧐 대본 평가", "📊 발표 능력 평가"])
    
    # (이전 코드와 동일하므로, 핵심만 유지하고 생략합니다. 
    #  실제 적용 시에는 아까 작성해 드린 [기능 1] 코드를 그대로 두시면 됩니다.)
    with tab1:
        st.write("발표 주제와 상황을 입력하면 AI가 대본을 써줍니다.")
        # ... (이전 코드의 대본 작성 로직) ...
        # (아까 코드가 있다면 그대로 유지하세요. 필요하면 다시 합쳐드립니다.)

# ==========================================
# [기능 2] 생기부 기반 대입 면접 (대폭 수정됨)
# ==========================================
elif menu == "2. 생기부 기반 대입 면접":
    st.title("🎓 생활기록부 기반 면접 (입학사정관 모드)")
    st.markdown("당신의 **생활기록부(PDF)**를 업로드하세요. AI 입학사정관이 내용을 분석해 **맞춤형 예상 질문**을 던집니다.")
    
    # 2.1 생기부 업로드
    uploaded_file = st.file_uploader("📂 생활기록부 PDF 업로드", type="pdf")
    
    if uploaded_file is not None:
        with st.spinner("📄 생기부 내용을 분석 중입니다..."):
            # PDF 텍스트 추출
            student_record_text = extract_text_from_pdf(uploaded_file)
            
            # 텍스트가 너무 짧으면 에러 처리
            if len(student_record_text) < 50:
                st.error("PDF에서 텍스트를 읽을 수 없습니다. 이미지로 된 PDF인가요?")
            else:
                st.success("✅ 분석 완료! 아래 버튼을 눌러 면접 질문을 생성하세요.")
                
                # 2.2 질문 생성 (GPT-4o 활용)
                if st.button("🤖 맞춤형 면접 질문 생성하기"):
                    prompt = f"""
                    당신은 대학 입학사정관입니다.
                    아래는 지원자의 생활기록부 내용 일부입니다.
                    
                    [생기부 내용]
                    {student_record_text[:3000]}  # (토큰 제한을 위해 3000자만 전송)
                    
                    위 내용을 바탕으로 지원자의 전공 적합성, 인성, 발전 가능성을 확인하기 위한 **날카로운 면접 질문 3가지**를 생성해주세요.
                    질문은 구체적이어야 하며, 생기부에 있는 특정 활동(동아리, 세특 등)을 언급하며 물어봐야 합니다.
                    """
                    
                    res = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    # 질문 저장
                    st.session_state['generated_questions'] = res.choices[0].message.content
    
    # 2.3 질문 선택 및 답변 연습
    if 'generated_questions' in st.session_state:
        st.markdown("---")
        st.subheader("🧐 AI 입학사정관의 예상 질문")
        st.info(st.session_state['generated_questions'])
        
        st.markdown("---")
        st.subheader("🎙️ 실전 답변 연습")
        st.caption("위 질문 중 하나를 골라 답변해 보세요.")
        
        target_q = st.text_input("답변할 질문을 여기에 복사해 넣으세요", placeholder="예: 2번 질문에 대해 답변하겠습니다.")
        
        audio_input = st.audio_input("🔴 녹음 시작")
        
        if audio_input and target_q:
            with st.spinner("입학사정관이 평가 중입니다..."):
                # STT
                audio_input.seek(0)
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_input).text
                
                st.markdown("### 🗣 내 답변")
                st.write(transcript)
                
                # GPT-4o 평가
                eval_prompt = f"""
                질문: {target_q}
                답변: {transcript}
                
                역할: 대학 입학사정관
                평가 기준:
                1. 구체성 (자신의 경험을 구체적으로 근거로 들었는가?)
                2. 진정성 (생기부 내용과 일관성이 있는가?)
                3. 논리성
                
                피드백을 주고 100점 만점으로 점수를 매기세요.
                """
                res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": eval_prompt}])
                
                st.markdown("### 🎓 평가 결과")
                st.write(res.choices[0].message.content)
