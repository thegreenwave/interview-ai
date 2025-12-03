import os
import time
import difflib
import numpy as np
import librosa
import streamlit as st
from openai import OpenAI
import plotly.graph_objects as go
import plotly.express as px
import pdfplumber
from pdf2image import convert_from_bytes
import pytesseract
from collections import Counter
import json

# ==========================================
# 🔑 설정 & 초기화
# ==========================================
st.set_page_config(page_title="Spec-trum Pro", page_icon="🎙️", layout="wide")

# 1. 네비게이션 상태 초기화
if 'step' not in st.session_state: st.session_state.step = 'login'

# 2. 데이터 공유용 세션 상태
if 'script' not in st.session_state: st.session_state.script = ""  # 생성된 대본 저장용

# 3. 화면 이동 함수
def go_to(page):
    st.session_state.step = page
    st.rerun()

# 4. API 키
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
client = OpenAI()

# ==========================================
# 📊 분석 엔진 (함수들)
# ==========================================
def analyze_audio_features(y, sr):
    rms = librosa.feature.rms(y=y)[0]
    times = librosa.times_like(rms, sr=sr)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    non_silent = librosa.effects.split(y, top_db=25)
    non_silent_dur = sum([(e-s) for s,e in non_silent]) / sr
    total_dur = librosa.get_duration(y=y, sr=sr)
    if len(non_silent) > 0: init_silence = librosa.frames_to_time(non_silent[0][0], sr=sr)
    else: init_silence = 0
    silence_ratio = (total_dur - non_silent_dur) / total_dur if total_dur > 0 else 0
    return times, rms, cent, total_dur, silence_ratio, init_silence

def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted: text += extracted + "\n"
    except: pass
    
    if len(text) < 50: # OCR fallback
        pdf_file.seek(0)
        try:
            images = convert_from_bytes(pdf_file.read())
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image, lang='kor+eng') + "\n"
        except: pass
    return text

def calculate_similarity(t1, t2):
    return difflib.SequenceMatcher(None, t1, t2).ratio() * 100

# ==========================================
# 🖥️ 화면 흐름 (Workflow)
# ==========================================

# [PAGE 1] 로그인
if st.session_state.step == 'login':
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("🔒 SPEC-TRUM")
        st.write("역량 전달의 스펙트럼을 넓히다")
        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인", use_container_width=True):
            if pw == "0601":
                st.success("접속 성공!")
                time.sleep(0.5)
                go_to('main_menu')
            else:
                st.error("비밀번호 오류")

# [PAGE 2] 메인 메뉴 (대분류)
elif st.session_state.step == 'main_menu':
    st.title("🚀 메인 메뉴")
    st.write("원하는 트레이닝 코스를 선택하세요.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("🎤 발표 마스터")
        if st.button("발표 준비 메뉴로 이동", use_container_width=True):
            go_to('pres_menu')
    with col2:
        st.info("🎓 생기부 면접")
        if st.button("면접 트레이닝 시작", use_container_width=True):
            go_to('inter_upload')

# =========================================================
# 🎤 [발표 트랙] - 서브 메뉴 및 독립 기능들
# =========================================================

# [PAGE 3-0] 발표 서브 메뉴 (3가지 독립 기능 선택)
elif st.session_state.step == 'pres_menu':
    st.title("🎤 발표 준비 메뉴")
    st.write("필요한 도구를 선택하세요.")
    
    # 3개의 카드로 나누어 배치
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("#### 📝 1. 대본 작성")
        st.caption("주제만 주면 AI가 써줍니다.")
        if st.button("대본 작성기 실행", use_container_width=True):
            go_to('pres_1_writer')
            
    with c2:
        st.markdown("#### 🧐 2. 대본 평가")
        st.caption("내가 쓴 대본을 피드백 받습니다.")
        if st.button("대본 평가기 실행", use_container_width=True):
            go_to('pres_2_advisor')
            
    with c3:
        st.markdown("#### 📊 3. 능력 평가")
        st.caption("녹음하고 속도, 발음, 톤 분석.")
        if st.button("능력 측정기 실행", use_container_width=True):
            go_to('pres_3_analyst')
            
    st.markdown("---")
    if st.button("⬅️ 메인 메뉴로 돌아가기", use_container_width=True):
        go_to('main_menu')

# [PAGE 3-1] 대본 작성기 (Writer)
elif st.session_state.step == 'pres_1_writer':
    st.title("📝 발표 대본 작성기")
    
    topic = st.text_input("주제", placeholder="예: 인공지능의 윤리적 문제")
    context = st.text_input("상황", placeholder="예: 윤리 수업 발표")
    req = st.text_area("요구사항", placeholder="서론-본론-결론, 3분 분량")
    
    if st.button("✨ 대본 생성 (GPT-4o-mini)", type="primary", use_container_width=True):
        if topic:
            with st.spinner("작성 중..."):
                prompt = f"주제:{topic}\n상황:{context}\n요구사항:{req}\n발표대본 작성해줘."
                res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user", "content":prompt}])
                st.session_state.script = res.choices[0].message.content # 생성된 대본 전역 저장
                st.success("생성 완료! 아래에서 확인하세요.")
        else:
            st.warning("주제를 입력하세요.")
            
    if st.session_state.script:
        st.text_area("생성된 대본 (복사해서 쓰세요)", st.session_state.script, height=300)
    
    st.markdown("---")
    if st.button("⬅️ 발표 메뉴로 복귀", use_container_width=True):
        go_to('pres_menu')

# [PAGE 3-2] 대본 평가기 (Advisor)
elif st.session_state.step == 'pres_2_advisor':
    st.title("🧐 대본 피드백")
    
    # 이전에 생성한 대본이 있으면 기본값으로 넣어줌
    default_text = st.session_state.script if st.session_state.script else ""
    user_script = st.text_area("평가받을 대본을 입력하세요", value=default_text, height=200)
    user_intent = st.text_input("의도하는 바 (강조점)")
    
    if st.button("🚀 피드백 받기", type="primary", use_container_width=True):
        if user_script:
            with st.spinner("분석 중..."):
                res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"user", "content":f"대본:{user_script}\n의도:{user_intent}\n평가해줘."}])
                st.info(res.choices[0].message.content)
        else:
            st.warning("대본을 입력하세요.")

    st.markdown("---")
    if st.button("⬅️ 발표 메뉴로 복귀", use_container_width=True):
        go_to('pres_menu')

# [PAGE 3-3] 능력 평가기 (Analyst)
elif st.session_state.step == 'pres_3_analyst':
    st.title("📊 발표 능력 정밀 분석")
    st.caption("대본이 있다면 정확도가 측정되고, 없으면 속도와 톤만 분석합니다.")
    
    ref_text = st.text_area("기준 대본 (선택사항 - 있으면 붙여넣으세요)", value=st.session_state.script, height=100)
    audio = st.audio_input("녹음 시작")
    
    if audio:
        with st.spinner("6-Point 정밀 분석 중..."):
            y, sr = librosa.load(audio, sr=None)
            times, rms, cent, tot_dur, _, _, _, _ = analyze_audio_features(y, sr)
            tempo = float(librosa.beat.beat_track(y=y, sr=sr)[0])
            
            # STT
            audio.seek(0)
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio).text
            
            # 정확도 (대본이 있을 때만)
            acc = calculate_similarity(ref_text, transcript) if ref_text else 0.0
            
            # 대시보드
            m1, m2, m3 = st.columns(3)
            m1.metric("속도", f"{tempo:.0f} BPM", delta="110~130 권장")
            m2.metric("정확도", f"{acc:.1f}%" if ref_text else "N/A")
            m3.metric("시간", f"{tot_dur:.1f}초")
            
            # 그래프
            st.subheader("목소리 크기 & 톤 변화")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=times, y=rms, fill='tozeroy', name='Volume', line=dict(color='firebrick')))
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("AI가 인식한 내용 보기"):
                st.write(transcript)

    st.markdown("---")
    if st.button("⬅️ 발표 메뉴로 복귀", use_container_width=True):
        go_to('pres_menu')

# =========================================================
# 🎓 [면접 트랙]
# =========================================================

# [PAGE 4-1] 생기부 업로드
elif st.session_state.step == 'inter_upload':
    st.title("📂 생기부 업로드")
    uploaded = st.file_uploader("PDF 파일 업로드", type="pdf")
    
    if uploaded:
        if st.button("질문 생성 및 다음 단계", type="primary", use_container_width=True):
            with st.spinner("분석 중..."):
                text = extract_text_from_pdf(uploaded)
                if len(text) > 50:
                    prompt = f"생기부 내용:\n{text[:15000]}\n면접 질문 3개 만들어줘."
                    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user", "content":prompt}])
                    st.session_state.uni_questions = res.choices[0].message.content
                    go_to('inter_practice')
                else:
                    st.error("텍스트 인식 실패. 이미지 PDF일 수 있습니다.")
    
    st.markdown("---")
    if st.button("⬅️ 메인 메뉴로", use_container_width=True):
        go_to('main_menu')

# [PAGE 4-2] 면접 실전 연습
elif st.session_state.step == 'inter_practice':
    st.title("🎙️ 실전 면접 트레이닝")
    st.info("AI 입학사정관의 예상 질문:")
    st.write(st.session_state.uni_questions)
    
    st.markdown("---")
    target_q = st.text_input("답변할 질문 입력")
    audio = st.audio_input("답변 녹음")
    
    if audio and target_q:
        with st.spinner("면접관 평가 중..."):
            audio.seek(0)
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio).text
            
            eval_prompt = f"질문:{target_q}\n답변:{transcript}\n평가:논리,진정,자신,적합. JSON출력."
            res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"user", "content":eval_prompt}], response_format={"type":"json_object"})
            data = json.loads(res.choices[0].message.content)
            
            st.subheader("평가 리포트")
            st.write(data.get('feedback'))
            
            cats = ['논리', '진정', '자신', '적합']
            vals = [data.get('logic',0)*10, data.get('sincerity',0)*10, data.get('confidence',0)*10, data.get('suitability',0)*10]
            fig = go.Figure(data=go.Scatterpolar(r=vals, theta=cats, fill='toself'))
            fig.update_layout(polar=dict(radialaxis=dict(range=[0,100])), showlegend=False)
            st.plotly_chart(fig)
            
    st.markdown("---")
    if st.button("⬅️ 다른 생기부 올리기", use_container_width=True):
        go_to('inter_upload')
