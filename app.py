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
from pdf2image import convert_from_bytes
import pytesseract

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
    # 로컬 테스트용 (Secrets가 없을 때 대비)
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
    
    # 첫 발화까지 걸린 시간 (Initial Delay) - 면접 긴장도 측정용
    if len(non_silent_intervals) > 0:
        initial_silence = librosa.frames_to_time(non_silent_intervals[0][0], sr=sr)
    else:
        initial_silence = 0
    
    silence_duration = total_duration - non_silent_duration
    silence_ratio = silence_duration / total_duration if total_duration > 0 else 0
    
    return times, rms, cent, total_duration, non_silent_duration, silence_duration, silence_ratio, initial_silence

def analyze_text_patterns(text):
    """텍스트에서 습관어(Filler)와 핵심 키워드 분석"""
    # 습관어 분석
    fillers = ["음", "어", "그", "막", "이제", "약간", "저", "사실"]
    filler_counts = {f: text.count(f) for f in fillers if text.count(f) > 0}
    total_fillers = sum(filler_counts.values())
    
    # 키워드 분석 (간단한 빈도수)
    words = text.replace(".", "").split()
    valid_words = [w for w in words if len(w) >= 2 and w not in fillers]
    top_keywords = Counter(valid_words).most_common(5)
    
    return filler_counts, total_fillers, top_keywords

def extract_text_from_pdf(pdf_file):
    """PDF 전체 페이지 텍스트 추출"""
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    # 페이지 제한 없이 전체 읽기 (비용 절감을 위해 요약 모델은 mini 사용 권장)
    for page in reader.pages: 
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

def calculate_similarity(text1, text2):
    """대본 일치도(정확성) 계산"""
    matcher = difflib.SequenceMatcher(None, text1, text2)
    return matcher.ratio() * 100

# ==========================================
# 🎛️ 메인 UI & 사이드바
# ==========================================
with st.sidebar:
    st.title("SPEC-TRUM")
    st.caption("역량 전달의 스펙트럼을 넓히다")
    st.markdown("---")
    menu = st.radio("기능 선택", ["1. 발표 준비 ", "2. 생기부 심층 면접"])
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
            p_topic = st.text_input("발표 주제, 주장", placeholder="예: 생성형 AI의 교육적 활용")
            p_context = st.text_input("발표 상황", placeholder="예: 프로그래밍 발표 수행평가")
        with col2:
            p_requirements = st.text_area("요구사항", placeholder="3분 발표, 서론-본론-결론 구조")
            
        if st.button("✨ 대본 생성하기 "):
            if not p_topic:
                st.warning("주제를 입력해주세요.")
            else:
                with st.spinner("발표대본을 작성중입니다..."):
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
        st.caption("대본과 실제 목소리를 비교하여 정밀 분석합니다.")
        
        ref_text = st.text_area("대본: ", value=st.session_state.get('script', ""), height=100)
        audio_input = st.audio_input("🔴 발표 녹음 시작")
        
        if audio_input and ref_text:
            with st.spinner("6-Point 정밀 분석 중..."):
                # 1. 오디오 분석
                y, sr = librosa.load(audio_input, sr=None)
                times, rms, cent, total_dur, _, silent_dur, silence_ratio, _ = analyze_audio_features(y, sr)
                tempo_arr, _ = librosa.beat.beat_track(y=y, sr=sr)
                tempo = float(tempo_arr)
                
                # 2. STT
                audio_input.seek(0)
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_input).text
                
                # 3. 텍스트 분석 (정확도, 습관어)
                accuracy = calculate_similarity(ref_text, transcript)
                filler_counts, total_fillers, top_keywords = analyze_text_patterns(transcript)
                
                # === 리포트 출력 ===
                st.markdown("---")
                # 섹션 1: 핵심 지표
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("속도 (BPM)", f"{tempo:.0f}", delta="권장 110~130")
                c2.metric("발음 정확도", f"{accuracy:.1f}%", delta="목표 90%")
                c3.metric("습관어(음/어)", f"{total_fillers}회", delta_color="inverse")
                c4.metric("발표 시간", f"{total_dur:.1f}초")
                
                st.markdown("---")
                # 섹션 2: 그래프
                g1, g2 = st.columns(2)
                with g1:
                    st.subheader("📈 다이내믹스 (톤 & 크기)")
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=times, y=rms, name='성량(Volume)', fill='tozeroy', line=dict(color='#EF4444')))
                    norm_cent = (cent - np.min(cent)) / (np.max(cent) - np.min(cent)) * np.max(rms)
                    fig.add_trace(go.Scatter(x=times, y=norm_cent, name='톤(Tone)', line=dict(color='#10B981'), opacity=0.5))
                    fig.update_layout(height=300, margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig, use_container_width=True)
                
                with g2:
                    st.subheader("🗣️ 발화 점유율")
                    fig_pie = px.pie(values=[total_dur-silent_dur, silent_dur], names=["말한 시간", "침묵"], 
                                     color_discrete_sequence=['#3B82F6', '#E5E7EB'], hole=0.4)
                    fig_pie.update_layout(height=300, margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig_pie, use_container_width=True)

                # 섹션 3: 키워드 & 습관어
                st.markdown("#### 🔑 키워드 & 습관어 분석")
                k1, k2 = st.columns(2)
                with k1:
                    st.write("**많이 쓴 단어 Top 5**")
                    st.write(top_keywords)
                with k2:
                    st.write("**감지된 습관어**")
                    st.write(filler_counts if filler_counts else "없음 (완벽합니다!)")
                
                with st.expander("내용 보기 (STT)"):
                    st.write(transcript)

# ==========================================
# [기능 2] 생기부 심층 면접 
# ==========================================
elif menu == "2. 생기부 심층 면접":
    st.title("🎓 생활기록부 기반 면접 (입학사정관)")
    st.markdown("생기부(PDF)를 업로드하면 AI가 전체를 분석하여 맞춤형 질문을 던집니다.")
    
    # 2.1 파일 업로드 및 질문 생성
    uploaded_file = st.file_uploader("생활기록부 PDF 업로드", type="pdf")
    
    if uploaded_file:
        with st.spinner("생기부 전체를 읽고 분석 중입니다... (Mini 모델로 비용 절감)"):
            text = extract_text_from_pdf(uploaded_file)
            
            if len(text) > 50:
                st.success(f"✅ 분석 완료! (총 {len(text)}자 읽음)")
                
                if st.button("🤖 맞춤형 질문 추출하기"):
                    # 💡 하이브리드 전략: 긴 텍스트 분석은 gpt-4o-mini 사용 (비용 1/20)
                    prompt = f"""
                    당신은 입학사정관입니다.
                    [생기부 내용 전체]
                    {text}

                    
                    지원자의 전공 적합성과 인성을 검증할 수 있는 날카로운 면접 질문 3가지를 만들어주세요.
                    생기부 내의 구체적인 활동(동아리, 세특, 독서 등)을 언급해야 합니다.
                    """
                    res = client.chat.completions.create(
                        model="gpt-4o-mini", # 👈 Mini 모델 사용!
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.session_state['uni_questions'] = res.choices[0].message.content
            else:
                st.error("텍스트를 읽을 수 없습니다. (암호 걸린 PDF인지 확인하세요)")

    # 2.2 질문 확인 및 답변
    if 'uni_questions' in st.session_state:
        st.info(st.session_state['uni_questions'])
        target_q = st.text_input("답변할 질문을 입력하세요", placeholder="위 질문 중 하나를 복사하세요.")

        audio_input = st.audio_input("🔴 답변 녹음 시작")
        
        if audio_input and target_q:
            with st.spinner("면접관이 평가 중입니다... (평가는 4o 사용)"):
                # 1. 오디오 분석
                y, sr = librosa.load(audio_input, sr=None)
                _, _, _, total_dur, _, _, _, initial_silence = analyze_audio_features(y, sr)
                tempo_arr, _ = librosa.beat.beat_track(y=y, sr=sr)
                tempo = float(tempo_arr)
                
                # 2. STT
                audio_input.seek(0)
                transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_input).text
                filler_counts, total_fillers, _ = analyze_text_patterns(transcript)
                
                # 3. GPT-4o 심층 평가 (JSON 출력)
                # 💡 평가는 짧은 텍스트이므로 정확한 gpt-4o 사용
                eval_prompt = f"""
                역할: 냉철한 입학사정관
                질문: {target_q}
                답변: {transcript}
                
                평가 항목(10점 만점): logic(논리성), sincerity(진정성/구체성), confidence(태도), suitability(전공적합성)
                피드백도 포함하여 JSON으로 출력.
                """
                res = client.chat.completions.create(
                    model="gpt-4o", # 👈 평가는 4o 사용!
                    messages=[{"role": "user", "content": eval_prompt}],
                    response_format={"type": "json_object"}
                )
                eval_data = json.loads(res.choices[0].message.content)
                
                # === 결과 리포트 ===
                st.markdown("---")
                
                # 섹션 1: 면접 지표
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("첫 반응 속도", f"{initial_silence:.1f}초", delta="3초 이내 권장", delta_color="inverse")
                m2.metric("습관어", f"{total_fillers}회", delta_color="inverse")
                m3.metric("말하기 속도", f"{tempo:.0f} BPM")
                m4.metric("답변 시간", f"{total_dur:.1f}초")
                
                # 섹션 2: 레이더 차트
                st.subheader("🕸️ 역량 평가 레이더")
                categories = ['논리성', '진정성', '자신감', '적합성']
                scores = [eval_data.get('logic', 0)*10, eval_data.get('sincerity', 0)*10, eval_data.get('confidence', 0)*10, eval_data.get('suitability', 0)*10]
                
                fig = go.Figure(data=go.Scatterpolar(r=scores, theta=categories, fill='toself', line_color='#4F46E5'))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=350)
                st.plotly_chart(fig, use_container_width=True)
                
                # 섹션 3: 피드백
                st.subheader("🧑‍💼 입학사정관 상세 피드백")
                st.info(eval_data.get('feedback', '피드백을 불러오지 못했습니다.'))
