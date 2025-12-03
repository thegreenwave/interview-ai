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
# 🔑 기본 설정 및 상태 초기화
# ==========================================
st.set_page_config(page_title="Spec-trum Pro", page_icon="🎙️", layout="wide")

# 1. 페이지 단계(Step) 초기화 (새로고침 해도 유지됨)
if 'step' not in st.session_state:
    st.session_state.step = 'login'  # 초기 화면: 로그인

# 2. 데이터 저장소 초기화
if 'script' not in st.session_state: st.session_state.script = ""
if 'uni_questions' not in st.session_state: st.session_state.uni_questions = ""
if 'target_q' not in st.session_state: st.session_state.target_q = ""

# 3. 페이지 이동 함수 (화면 전환의 핵심)
def go_to(page_name):
    st.session_state.step = page_name
    st.rerun()  # 화면을 즉시 새로고침해서 이전 화면을 지움

# 4. API 키 설정
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
client = OpenAI()

# ==========================================
# 📊 분석 함수 (이전과 동일)
# ==========================================
def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted: text += extracted + "\n"
    except: pass

    if len(text) < 50:
        st.toast("⚠️ 이미지 PDF 감지! OCR 변환 중...")
        pdf_file.seek(0)
        try:
            images = convert_from_bytes(pdf_file.read())
            text = ""
            for image in images:
                page_text = pytesseract.image_to_string(image, lang='kor+eng')
                text += page_text + "\n"
        except: return ""
    return text

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

def analyze_text_patterns(text):
    fillers = ["음", "어", "그", "막", "이제", "약간", "저", "사실"]
    cnt = {f: text.count(f) for f in fillers if text.count(f) > 0}
    return cnt, sum(cnt.values())

def calculate_similarity(t1, t2):
    return difflib.SequenceMatcher(None, t1, t2).ratio() * 100

# ==========================================
# 🖥️ 페이지별 화면 구성 (Web Flow)
# ==========================================

# [PAGE 1] 로그인 화면
if st.session_state.step == 'login':
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("🔒 SPEC-TRUM")
        st.write("역량을 증명하는 가장 확실한 방법")
        pw = st.text_input("접속 비밀번호", type="password")
        
        if st.button("로그인", use_container_width=True):
            if pw == "0601":
                st.success("로그인 성공!")
                time.sleep(0.5)
                go_to('main_menu') # 메인 메뉴로 이동
            else:
                st.error("비밀번호가 틀렸습니다.")

# [PAGE 2] 메인 메뉴 (기능 선택)
elif st.session_state.step == 'main_menu':
    st.title("🚀 기능을 선택하세요")
    st.write("어떤 연습을 하시겠습니까?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("🎤 발표 준비")
        st.write("주제만 주면 대본 작성부터 평가까지!")
        if st.button("발표 마스터 시작하기", use_container_width=True):
            go_to('pres_input') # 발표 입력 화면으로 이동

    with col2:
        st.info("🎓 생기부 면접")
        st.write("PDF를 올리면 나만을 위한 질문 생성!")
        if st.button("심층 면접 시작하기", use_container_width=True):
            go_to('inter_upload') # 면접 업로드 화면으로 이동

# =========================================================
# 🎤 [발표 트랙] 
# =========================================================

# [PAGE 3-1] 발표: 정보 입력
elif st.session_state.step == 'pres_input':
    st.title("📝 발표 정보 입력")
    
    topic = st.text_input("발표 주제", placeholder="예: 생성형 AI의 미래")
    context = st.text_input("상황", placeholder="예: 수행평가 3분 발표")
    req = st.text_area("요구사항", placeholder="서론-본론-결론 구조로 써줘")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("⬅️ 이전 (메인메뉴)", use_container_width=True):
            go_to('main_menu')
    with c2:
        if st.button("✨ 대본 생성 및 다음 단계", type="primary", use_container_width=True):
            if not topic:
                st.warning("주제를 입력해주세요.")
            else:
                with st.spinner("AI가 대본을 작성 중입니다..."):
                    prompt = f"주제:{topic}\n상황:{context}\n요구사항:{req}\n발표대본 작성해줘."
                    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user", "content":prompt}])
                    st.session_state.script = res.choices[0].message.content
                    go_to('pres_result') # 결과 화면으로 이동

# [PAGE 3-2] 발표: 연습 및 평가
elif st.session_state.step == 'pres_result':
    st.title("📊 실전 발표 연습")
    
    # 상단: 대본 확인
    with st.expander("📄 생성된 대본 보기 (클릭)", expanded=False):
        st.text_area("대본", st.session_state.script, height=200)

    st.write("대본을 보며 녹음하세요.")
    audio = st.audio_input("녹음 시작")
    
    if audio:
        with st.spinner("정밀 분석 중..."):
            y, sr = librosa.load(audio, sr=None)
            times, rms, cent, tot_dur, _, _, _, _ = analyze_audio_features(y, sr)
            tempo = float(librosa.beat.beat_track(y=y, sr=sr)[0])
            
            audio.seek(0)
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio).text
            acc = calculate_similarity(st.session_state.script, transcript)
            
            # 결과 표시
            m1, m2, m3 = st.columns(3)
            m1.metric("속도", f"{tempo:.0f} BPM")
            m2.metric("정확도", f"{acc:.1f}%")
            m3.metric("시간", f"{tot_dur:.1f}초")
            
            st.subheader("다이내믹스 그래프")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=times, y=rms, fill='tozeroy', name='Volume'))
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    if st.button("⬅️ 처음으로 (주제 다시 입력)", use_container_width=True):
        go_to('pres_input')


# =========================================================
# 🎓 [면접 트랙]
# =========================================================

# [PAGE 4-1] 면접: 파일 업로드
elif st.session_state.step == 'inter_upload':
    st.title("📂 생기부 업로드")
    
    uploaded = st.file_uploader("PDF 파일 업로드", type="pdf")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("⬅️ 이전 (메인메뉴)", use_container_width=True):
            go_to('main_menu')
    with c2:
        if uploaded:
            if st.button("🤖 질문 생성 및 다음 단계", type="primary", use_container_width=True):
                with st.spinner("생기부 분석 중..."):
                    text = extract_text_from_pdf(uploaded)
                    if len(text) > 50:
                        prompt = f"생기부 내용:\n{text[:15000]}\n면접 질문 3개 만들어줘."
                        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user", "content":prompt}])
                        st.session_state.uni_questions = res.choices[0].message.content
                        go_to('inter_result')
                    else:
                        st.error("텍스트 인식 실패.")
        else:
            st.info("파일을 먼저 업로드해주세요.")

# [PAGE 4-2] 면접: 실전 연습
elif st.session_state.step == 'inter_result':
    st.title("🎙️ 실전 면접 트레이닝")
    
    st.info("AI가 생성한 질문입니다.")
    st.write(st.session_state.uni_questions)
    
    st.markdown("---")
    target_q = st.text_input("답변할 질문을 입력/복사하세요")
    audio = st.audio_input("답변 녹음")
    
    if audio and target_q:
        with st.spinner("면접관 평가 중..."):
            audio.seek(0)
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio).text
            
            eval_prompt = f"질문:{target_q}\n답변:{transcript}\n평가항목: 논리성, 진정성, 자신감, 적합성. JSON 출력."
            res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"user", "content":eval_prompt}], response_format={"type":"json_object"})
            data = json.loads(res.choices[0].message.content)
            
            st.subheader("평가 결과")
            st.write(data.get('feedback'))
            
            # 차트
            cats = ['논리', '진정', '자신', '적합']
            vals = [data.get('logic',0)*10, data.get('sincerity',0)*10, data.get('confidence',0)*10, data.get('suitability',0)*10]
            fig = go.Figure(data=go.Scatterpolar(r=vals, theta=cats, fill='toself'))
            fig.update_layout(polar=dict(radialaxis=dict(range=[0,100])), showlegend=False)
            st.plotly_chart(fig)

    st.markdown("---")
    if st.button("⬅️ 다른 생기부 올리기", use_container_width=True):
        go_to('inter_upload')
