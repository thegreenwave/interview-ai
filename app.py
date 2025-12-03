import os
import random
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
# 🔑 기본 설정
# ==========================================
st.set_page_config(page_title="Spec-trum Pro", page_icon="🎙️", layout="wide")

password = st.text_input("🔒 접속 비밀번호를 입력하세요", type="password")
if password != "0601": 
    st.warning("비밀번호가 틀렸습니다.")
    st.stop()

if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
else:
    pass

client = OpenAI()

# ==========================================
# 📊 분석 함수 모음
# ==========================================
def extract_text_from_pdf(pdf_file):
    """
    하이브리드 추출 방식:
    1. 텍스트 레이어가 있으면 바로 읽음 (빠름)
    2. 없으면(이미지면) OCR로 강제로 읽음 (느림 but 확실)
    """
    text = ""
    
    # 1. 먼저 일반적인 방식으로 시도 (pdfplumber)
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except:
        pass 

    # 2. 텍스트가 너무 적으면(50자 미만) 이미지로 간주하고 OCR 수행
    if len(text) < 50:
        st.toast("⚠️ 이미지 PDF가 감지되었습니다. OCR 변환을 시도합니다. (시간이 좀 걸려요!)")
        
        # 파일 포인터 초기화
        pdf_file.seek(0)
        
        # PDF를 이미지로 변환 (메모리 내 처리)
        try:
            images = convert_from_bytes(pdf_file.read())
            text = ""
            # 각 이미지를 순회하며 한글 추출
            for image in images:
                page_text = pytesseract.image_to_string(image, lang='kor+eng')
                text += page_text + "\n"
        except Exception as e:
            st.error(f"OCR 변환 중 오류 발생: {e}")
            return ""
            
    return text

def analyze_audio_features(y, sr):
    rms = librosa.feature.rms(y=y)[0]
    times = librosa.times_like(rms, sr=sr)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    non_silent_intervals = librosa.effects.split(y, top_db=25)
    non_silent_duration = sum([(end - start) for start, end in non_silent_intervals]) / sr
    total_duration = librosa.get_duration(y=y, sr=sr)
    
    if len(non_silent_intervals) > 0:
        initial_silence = librosa.frames_to_time(non_silent_intervals[0][0], sr=sr)
    else:
        initial_silence = 0
    
    silence_duration = total_duration - non_silent_duration
    silence_ratio = silence_duration / total_duration if total_duration > 0 else 0
    
    return times, rms, cent, total_duration, non_silent_duration, silence_duration, silence_ratio, initial_silence

def analyze_text_patterns(text):
    fillers = ["음", "어", "그", "막", "이제", "약간", "저", "사실"]
    filler_counts = {f: text.count(f) for f in fillers if text.count(f) > 0}
    total_fillers = sum(filler_counts.values())
    words = text.replace(".", "").split()
    valid_words = [w for w in words if len(w) >= 2 and w not in fillers]
    top_keywords = Counter(valid_words).most_common(5)
    return filler_counts, total_fillers, top_keywords

def calculate_similarity(text1, text2):
    matcher = difflib.SequenceMatcher(None, text1, text2)
    return matcher.ratio() * 100

# ==========================================
# 🎛️ 메인 UI
# ==========================================
with st.sidebar:
    st.title("SPEC-TRUM")
    st.caption("OCR 엔진 탑재 버전")
    st.markdown("---")
    menu = st.radio("기능 선택", ["1. 발표 준비", "2. 생기부 심층 면접"])

# ==========================================
# [기능 1] 발표 준비
# ==========================================
if menu == "1. 발표 준비":
    st.title("🎤 발표 준비")
    tab1, tab2, tab3 = st.tabs(["📝 대본 작성", "🧐 대본 평가", "📊 발표 능력 평가"])
    
    with tab1:
        st.header("대본 작성")
        col1, col2 = st.columns(2)
        with col1:
            p_topic = st.text_input("주제", placeholder="주제 입력")
            p_context = st.text_input("상황", placeholder="상황 입력")
        with col2:
            p_req = st.text_area("요구사항", placeholder="요구사항 입력")
            
        if st.button("대본 생성"):
            if p_topic:
                with st.spinner("작성 중..."):
                    prompt = f"주제:{p_topic}\n상황:{p_context}\n요구사항:{p_req}\n발표대본 작성해줘."
                    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user", "content":prompt}])
                    st.session_state['script'] = res.choices[0].message.content
                    st.success("완료!")

        if 'script' in st.session_state:
            st.text_area("생성된 대본", st.session_state['script'])

    with tab2:
        st.header("대본 평가")
        u_script = st.text_area("대본 입력", value=st.session_state.get('script', ""))
        u_intent = st.text_input("의도")
        if st.button("평가 받기") and u_script:
            with st.spinner("평가 중..."):
                res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"user", "content":f"대본:{u_script}\n의도:{u_intent}\n평가해줘."}])
                st.info(res.choices[0].message.content)

    with tab3:
        st.header("발표 능력 평가")
        ref_text = st.text_area("기준 대본", value=st.session_state.get('script', ""), height=100)
        audio_input = st.audio_input("녹음 시작")
        if audio_input and ref_text:
            with st.spinner("분석 중..."):
                y, sr = librosa.load(audio_input, sr=None)
                times, rms, cent, total_dur, _, _, _, _ = analyze_audio_features(y, sr)
                tempo = float(librosa.beat.beat_track(y=y, sr=sr)[0])
                audio_input.seek(0)
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_input).text
                acc = calculate_similarity(ref_text, transcript)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("속도", f"{tempo:.0f} BPM")
                c2.metric("정확도", f"{acc:.1f}%")
                c3.metric("시간", f"{total_dur:.1f}초")
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=times, y=rms, fill='tozeroy', name='Volume'))
                st.plotly_chart(fig, use_container_width=True)

# ==========================================
# [기능 2] 생기부 심층 면접 (OCR 적용)
# ==========================================
elif menu == "2. 생기부 심층 면접":
    st.title("🎓 생활기록부 기반 면접")
    st.markdown("이미지로 된 PDF도 읽을 수 있습니다. (OCR 엔진 가동)")
    
    uploaded_file = st.file_uploader("생기부 PDF 업로드", type="pdf")
    
    if uploaded_file:
        with st.spinner("생기부를 읽고 있습니다... (이미지일 경우 1~2분 소요될 수 있습니다)"):
            text = extract_text_from_pdf(uploaded_file)
            
            if len(text) > 50:
                st.success(f"✅ 분석 완료! (총 {len(text)}자 읽음)")
                if st.button("질문 생성하기"):
                    prompt = f"생기부 내용:\n{text[:15000]}\n전공적합성/인성 면접 질문 3개 만들어줘."
                    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user", "content":prompt}])
                    st.session_state['uni_questions'] = res.choices[0].message.content
            else:
                st.error("이미지 변환에 실패했거나 내용이 없습니다.")

    if 'uni_questions' in st.session_state:
        st.info(st.session_state['uni_questions'])
        target_q = st.text_input("질문 입력")
        audio_input = st.audio_input("녹음")
        if audio_input and target_q:
            with st.spinner("평가 중..."):
                audio_input.seek(0)
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_input).text
                
                eval_prompt = f"질문:{target_q}\n답변:{transcript}\n평가항목: 논리성, 진정성, 자신감, 적합성. JSON으로 점수와 피드백 줘."
                res = client.chat.completions.create(model="gpt-4o", messages=[{"role":"user", "content":eval_prompt}], response_format={"type":"json_object"})
                eval_data = json.loads(res.choices[0].message.content)
                
                st.write(eval_data.get('feedback'))
                
                # 레이더 차트
                categories = ['논리성', '진정성', '자신감', '적합성']
                scores = [eval_data.get('logic',0)*10, eval_data.get('sincerity',0)*10, eval_data.get('confidence',0)*10, eval_data.get('suitability',0)*10]
                fig = go.Figure(data=go.Scatterpolar(r=scores, theta=categories, fill='toself'))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
                st.plotly_chart(fig)
