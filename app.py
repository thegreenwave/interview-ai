import os
import time
import io
import difflib
import librosa
import streamlit as st
from openai import OpenAI
import plotly.graph_objects as go
import pdfplumber
from pdf2image import convert_from_bytes
import pytesseract
import json
import pandas as pd


# -------------------------------------------------
# 🔑 Streamlit & OpenAI 기본 세팅
# -------------------------------------------------
st.set_page_config(page_title="Spec-trum Pro", page_icon="🎙️", layout="wide")

# 네비게이션 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = "login"

# 생성된 대본 저장용
if "script" not in st.session_state:
    st.session_state.script = ""

# 면접 질문 원문 / 리스트 / 현재 인덱스 / 기록
if "uni_questions" not in st.session_state:
    st.session_state.uni_questions = ""
if "uni_q_list" not in st.session_state:
    st.session_state.uni_q_list = []
if "current_q_idx" not in st.session_state:
    st.session_state.current_q_idx = 0
if "interview_records" not in st.session_state:
    st.session_state.interview_records = []

# 화면 이동 함수
def go_to(page: str):
    st.session_state.step = page
    st.rerun()

# OpenAI API 키 설정
# - secrets.toml 에 [default] OPENAI_API_KEY="..." 로 넣어두었다고 가정
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# 🔑 여기서 OpenAI 클라이언트 생성 (API 키는 환경변수 또는 secrets에서 읽음)
client = OpenAI()


# -------------------------------------------------
# 📊 분석 엔진 (함수들)
# -------------------------------------------------
def analyze_audio_features(y, sr):
    """
    음성 신호 y와 샘플링레이트 sr을 받아
    - RMS(볼륨)
    - 시간축
    - 스펙트럴 센트로이드
    - 전체 길이
    - 침묵 비율
    - 초기 침묵 시간
    을 계산한다.
    """
    rms = librosa.feature.rms(y=y)[0]
    times = librosa.times_like(rms, sr=sr)
    cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]

    # 비침묵 구간 탐지
    non_silent = librosa.effects.split(y, top_db=25)
    non_silent_dur = sum((e - s) for s, e in non_silent) / sr
    total_dur = librosa.get_duration(y=y, sr=sr)

    if len(non_silent) > 0:
        # non_silent는 샘플 인덱스를 반환하므로 sr로 나눠서 초로 변환
        init_silence = non_silent[0][0] / sr
    else:
        init_silence = 0.0

    silence_ratio = (
        (total_dur - non_silent_dur) / total_dur if total_dur > 0 else 0.0
    )

    return times, rms, cent, total_dur, silence_ratio, init_silence


def extract_text_from_pdf(pdf_file):
    """
    pdfplumber로 텍스트 추출을 시도하고,
    텍스트가 너무 적으면 pdf2image + Tesseract로 OCR을 시도한다.
    """
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except Exception:
        pass

    # 텍스트가 너무 적으면 OCR 시도
    if len(text) < 50:
        pdf_file.seek(0)
        try:
            images = convert_from_bytes(pdf_file.read())
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image, lang="kor+eng") + "\n"
        except Exception:
            pass

    return text


def calculate_similarity(t1, t2):
    """
    두 문자열의 유사도를 0~100 (%)로 반환.
    """
    return difflib.SequenceMatcher(None, t1, t2).ratio() * 100


def text_to_speech_bytes(text: str) -> bytes:
    """
    OpenAI Audio TTS를 사용해 질문을 음성으로 변환하고,
    MP3 바이트를 반환한다.
    ⚠️ 사용 중인 openai-python SDK 버전에 따라 model 이름이나 속성이 다를 수 있음.
       필요하면 공식 문서를 보고 model/필드를 조정해야 함.
    """
    try:
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",  # 또는 "tts-1", "gpt-4o-audio-preview" 등 환경에 맞게 수정
            voice="alloy",
            input=text,
        )
        # 최신 SDK 기준: response.read() 또는 stream_to_file 등을 제공.
        # 여기서는 bytes로 가정.
        audio_bytes = response.read()
        return audio_bytes
    except Exception as e:
        st.warning(f"TTS 생성 중 오류가 발생했습니다: {e}")
        return b""


# -------------------------------------------------
# 🖥️ 화면 흐름 (Workflow)
# -------------------------------------------------

# [PAGE 1] 로그인
if st.session_state.step == "login":
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🔒 SPEC-TRUM")
        st.write("역량 전달의 스펙트럼을 넓히다")

        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인", use_container_width=True):
            if pw == "0601":
                st.success("접속 성공!")
                time.sleep(0.5)
                go_to("main_menu")
            else:
                st.error("비밀번호 오류")

# [PAGE 2] 메인 메뉴 (대분류)
elif st.session_state.step == "main_menu":
    st.title("🚀 메인 메뉴")
    st.write("원하는 트레이닝 코스를 선택하세요.")

    col1, col2 = st.columns(2)
    with col1:
        st.info("🎤 발표 마스터")
        if st.button("발표 준비 메뉴로 이동", use_container_width=True):
            go_to("pres_menu")
    with col2:
        st.info("🎓 생기부 면접")
        if st.button("면접 트레이닝 시작", use_container_width=True):
            go_to("inter_upload")

# =========================================================
# 🎤 [발표 트랙] - 서브 메뉴 및 독립 기능들
# =========================================================

# [PAGE 3-0] 발표 서브 메뉴 (3가지 독립 기능 선택)
elif st.session_state.step == "pres_menu":
    st.title("🎤 발표 준비 메뉴")
    st.write("필요한 도구를 선택하세요.")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("#### 📝 1. 대본 작성")
        st.caption("주제만 주면 AI가 써줍니다.")
        if st.button("대본 작성기 실행", use_container_width=True):
            go_to("pres_1_writer")

    with c2:
        st.markdown("#### 🧐 2. 대본 평가")
        st.caption("내가 쓴 대본을 피드백 받습니다.")
        if st.button("대본 평가기 실행", use_container_width=True):
            go_to("pres_2_advisor")

    with c3:
        st.markdown("#### 📊 3. 능력 평가")
        st.caption("녹음하고 속도, 발음, 톤 분석.")
        if st.button("능력 측정기 실행", use_container_width=True):
            go_to("pres_3_analyst")

    st.markdown("---")
    if st.button("⬅️ 메인 메뉴로 돌아가기", use_container_width=True):
        go_to("main_menu")

# [PAGE 3-1] 대본 작성기 (Writer)
elif st.session_state.step == "pres_1_writer":
    st.title("📝 발표 대본 작성기")

    topic = st.text_input("주제", placeholder="예: 인공지능의 윤리적 문제")
    context = st.text_input("상황", placeholder="예: 윤리 수업 발표")
    req = st.text_area("요구사항", placeholder="서론-본론-결론, 3분 분량")

    if st.button("✨ 대본 생성 (GPT-4o-mini)", type="primary", use_container_width=True):
        if not topic:
            st.warning("주제를 입력해 주세요.")
        else:
            with st.spinner("작성 중..."):
                prompt = (
                    f"주제: {topic}\n"
                    f"상황: {context}\n"
                    f"요구사항: {req}\n"
                    "위 정보를 바탕으로 발표 대본을 한국어로 작성해줘."
                )
                try:
                    res = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                    )
                    st.session_state.script = res.choices[0].message.content
                    st.success("생성 완료! 아래에서 확인하세요.")
                except Exception as e:
                    st.error(f"대본 생성 중 오류가 발생했습니다: {e}")

    if st.session_state.script:
        st.text_area(
            "생성된 대본 (복사해서 쓰세요)",
            st.session_state.script,
            height=300,
        )

    st.markdown("---")
    if st.button("⬅️ 발표 메뉴로 복귀", use_container_width=True):
        go_to("pres_menu")

# [PAGE 3-2] 대본 평가기 (Advisor)
elif st.session_state.step == "pres_2_advisor":
    st.title("🧐 대본 피드백")

    default_text = st.session_state.script or ""
    user_script = st.text_area(
        "평가받을 대본을 입력하세요",
        value=default_text,
        height=200,
    )
    user_intent = st.text_input("의도하는 바 (강조점)")

    if st.button("🚀 피드백 받기", type="primary", use_container_width=True):
        if not user_script.strip():
            st.warning("대본을 입력하세요.")
        else:
            with st.spinner("분석 중..."):
                prompt = (
                    f"다음 발표 대본을 평가해줘.\n\n"
                    f"[대본]\n{user_script}\n\n"
                    f"[발표자가 전달하고 싶은 의도]\n{user_intent}\n"
                    "- 논리 구조\n- 전달력\n- 청중 이해도\n- 개선점\n을 중심으로 피드백해줘."
                )
                try:
                    res = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                    )
                    st.info(res.choices[0].message.content)
                except Exception as e:
                    st.error(f"피드백 생성 중 오류가 발생했습니다: {e}")

    st.markdown("---")
    if st.button("⬅️ 발표 메뉴로 복귀", use_container_width=True):
        go_to("pres_menu")

# [PAGE 3-3] 능력 평가기 (Analyst)
elif st.session_state.step == "pres_3_analyst":
    st.title("📊 발표 능력 정밀 분석")
    st.caption("대본이 있다면 정확도가 측정되고, 없으면 속도와 톤만 분석합니다.")

    ref_text = st.text_area(
        "기준 대본 (선택사항 - 있으면 붙여넣으세요)",
        value=st.session_state.script,
        height=100,
    )
    audio = st.audio_input("녹음 시작")

    if audio:
        with st.spinner("정밀 분석 중..."):
            try:
                # 오디오 로드
                y, sr = librosa.load(audio, sr=None)
                times, rms, cent, tot_dur, silence_ratio, init_silence = analyze_audio_features(
                    y, sr
                )
                tempo = float(librosa.beat.beat_track(y=y, sr=sr)[0])

                # 피치(f0) 추정
                f0 = librosa.yin(
                    y,
                    fmin=librosa.note_to_hz("C2"),
                    fmax=librosa.note_to_hz("C7"),
                )
                t_pitch = librosa.times_like(f0, sr=sr)

                # STT
                audio.seek(0)
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                ).text

                # 정확도 (대본이 있을 때만)
                acc = (
                    calculate_similarity(ref_text, transcript)
                    if ref_text.strip()
                    else 0.0
                )

                # 대시보드 메트릭
                m1, m2, m3 = st.columns(3)
                m1.metric("속도", f"{tempo:.0f} BPM", delta="110~130 권장")
                m2.metric(
                    "정확도",
                    f"{acc:.1f}%" if ref_text.strip() else "N/A",
                )
                m3.metric("발표 시간", f"{tot_dur:.1f}초")

                m4, m5 = st.columns(2)
                m4.metric("침묵 비율", f"{silence_ratio * 100:.1f}%")
                m5.metric("초기 침묵 시간", f"{init_silence:.1f}초")

                # 그래프 1: 볼륨 변화
                st.subheader("목소리 크기 변화 (RMS)")
                fig_vol = go.Figure()
                fig_vol.add_trace(
                    go.Scatter(
                        x=times,
                        y=rms,
                        fill="tozeroy",
                        name="Volume",
                        line=dict(color="firebrick"),
                    )
                )
                fig_vol.update_layout(
                    xaxis_title="시간 (s)",
                    yaxis_title="상대 볼륨 (RMS)",
                    template="plotly_white",
                )
                st.plotly_chart(fig_vol, use_container_width=True)

                # 그래프 2: 피치 변화
                st.subheader("피치(음높이) 변화")
                fig_pitch = go.Figure()
                fig_pitch.add_trace(
                    go.Scatter(
                        x=t_pitch,
                        y=f0,
                        name="Pitch (Hz)",
                    )
                )
                fig_pitch.update_layout(
                    xaxis_title="시간 (s)",
                    yaxis_title="기초 주파수 (Hz)",
                    template="plotly_white",
                )
                st.plotly_chart(fig_pitch, use_container_width=True)

                # 그래프 3: 스펙트럴 센트로이드 (발음/명료도 경향)
                st.subheader("발음/명료도 경향 (스펙트럴 센트로이드)")
                t_cent = librosa.times_like(cent, sr=sr)
                fig_cent = go.Figure()
                fig_cent.add_trace(
                    go.Scatter(
                        x=t_cent,
                        y=cent,
                        name="Spectral Centroid",
                    )
                )
                fig_cent.update_layout(
                    xaxis_title="시간 (s)",
                    yaxis_title="중심 주파수 (Hz 대역)",
                    template="plotly_white",
                )
                st.plotly_chart(fig_cent, use_container_width=True)

                with st.expander("AI가 인식한 내용 보기 (Whisper STT 결과)"):
                    st.write(transcript)

            except Exception as e:
                st.error(f"오디오 분석 중 오류가 발생했습니다: {e}")

    st.markdown("---")
    if st.button("⬅️ 발표 메뉴로 복귀", use_container_width=True):
        go_to("pres_menu")

# =========================================================
# 🎓 [면접 트랙]
# =========================================================

# [PAGE 4-1] 생기부 업로드
elif st.session_state.step == "inter_upload":
    st.title("📂 생기부 업로드")
    uploaded = st.file_uploader("PDF 파일 업로드", type="pdf")

    if uploaded:
        if st.button("질문 생성 및 다음 단계", type="primary", use_container_width=True):
            with st.spinner("생기부를 분석해 면접 질문을 생성 중입니다..."):
                text = extract_text_from_pdf(uploaded)
                if len(text) > 50:
                    prompt = (
                        "다음 생기부 내용을 바탕으로, 학생부 종합전형 면접에서 나올 법한 예상 질문 10개를 "
                        "한국어로 만들어줘. 각 질문은 한 줄에 하나씩 써줘.\n\n"
                        f"[생기부 내용]\n{text[:15000]}"
                    )
                    try:
                        res = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": prompt}],
                        )
                        q_text = res.choices[0].message.content
                        st.session_state.uni_questions = q_text

                        # 줄 단위로 나누고, "?"가 포함된 줄만 질문으로 간주
                        lines = [ln.strip("-• ").strip() for ln in q_text.splitlines()]
                        q_list = [ln for ln in lines if "?" in ln]
                        st.session_state.uni_q_list = q_list
                        st.session_state.current_q_idx = 0

                        go_to("inter_practice")
                    except Exception as e:
                        st.error(f"질문 생성 중 오류가 발생했습니다: {e}")
                else:
                    st.error("텍스트 인식 실패. 이미지 PDF일 가능성이 높습니다. 스캔 품질을 확인해 주세요.")

    st.markdown("---")
    if st.button("⬅️ 메인 메뉴로", use_container_width=True):
        go_to("main_menu")

# [PAGE 4-2] 면접 실전 연습
elif st.session_state.step == "inter_practice":
    st.title("🎙️ 실전 면접 트레이닝")

    questions_text = st.session_state.get(
        "uni_questions", "아직 생성된 질문이 없습니다. 이전 단계에서 생기부를 업로드해 주세요."
    )
    q_list = st.session_state.get("uni_q_list", [])

    st.info("AI 입학사정관의 예상 질문 (원문):")
    st.write(questions_text)

    st.markdown("---")

    if not q_list:
        st.warning("질문 리스트를 찾을 수 없습니다. 이전 단계에서 다시 질문을 생성해 주세요.")
    else:
        # 현재 질문 선택 (번호 기반)
        max_q = len(q_list)
        current_q_number = st.number_input(
            "연습할 질문 번호 선택",
            min_value=1,
            max_value=max_q,
            value=st.session_state.current_q_idx + 1,
            step=1,
        )
        st.session_state.current_q_idx = int(current_q_number) - 1
        current_question = q_list[st.session_state.current_q_idx]

        st.subheader(f"질문 {current_q_number} / {max_q}")
        st.write(current_question)

        # 타이머 설정
        answer_seconds = st.slider("답변 시간 설정 (초)", 30, 180, 60, step=10)

        # 질문 읽기 + 타이머 시작
        if st.button("⏱ 질문 읽기 & 타이머 시작", type="primary"):
            # 질문 TTS (가능한 경우)
            audio_bytes = text_to_speech_bytes(current_question)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")

            # 간단 카운트다운 타이머 (시각적 가이드)
            timer_placeholder = st.empty()
            for remaining in range(answer_seconds, 0, -1):
                timer_placeholder.markdown(
                    f"### ⏳ 남은 시간: **{remaining}초**"
                )
                time.sleep(1)
            timer_placeholder.markdown("### ✅ 답변 시간 종료!")

        st.markdown("---")
        st.markdown("#### 🎤 답변 녹음 및 평가")

        audio = st.audio_input("질문에 대한 답변을 녹음하세요")

        if audio:
            with st.spinner("면접관 평가 중..."):
                try:
                    audio.seek(0)
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio,
                    ).text

                    eval_prompt = (
                        "너는 학생부 종합전형 면접관이다.\n"
                        "다음 질문과 답변을 보고, 논리성, 진정성, 자신감, 지원전공 적합성을 0~10점으로 평가하고, "
                        "짧은 피드백을 JSON 형식으로 출력해라.\n\n"
                        f"[질문]\n{current_question}\n\n"
                        f"[답변(STT 결과)]\n{transcript}\n\n"
                        '출력 형식 예시: {"logic": 7, "sincerity": 8, "confidence": 6, '
                        '"suitability": 7, "feedback": "한 줄 이상의 코멘트"}'
                    )

                    res = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": eval_prompt}],
                        response_format={"type": "json_object"},
                    )
                    data = json.loads(res.choices[0].message.content)

                    st.subheader("평가 리포트")
                    st.write(data.get("feedback", "별도의 피드백이 제공되지 않았습니다."))

                    cats = ["논리", "진정", "자신", "적합"]
                    vals = [
                        data.get("logic", 0) * 10,
                        data.get("sincerity", 0) * 10,
                        data.get("confidence", 0) * 10,
                        data.get("suitability", 0) * 10,
                    ]

                    fig = go.Figure(
                        data=go.Scatterpolar(
                            r=vals,
                            theta=cats,
                            fill="toself",
                            name="면접 역량",
                        )
                    )
                    fig.update_layout(
                        polar=dict(radialaxis=dict(range=[0, 100])),
                        showlegend=False,
                        template="plotly_white",
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    with st.expander("AI가 인식한 답변 텍스트 (Whisper 결과)"):
                        st.write(transcript)

                    # 👉 기록용 레포트에 이 세션 추가
                    record = {
                        "question_number": int(current_q_number),
                        "question": current_question,
                        "transcript": transcript,
                        "logic": data.get("logic", 0),
                        "sincerity": data.get("sincerity", 0),
                        "confidence": data.get("confidence", 0),
                        "suitability": data.get("suitability", 0),
                        "feedback": data.get("feedback", ""),
                    }
                    st.session_state.interview_records.append(record)

                except Exception as e:
                    st.error(f"면접 평가 중 오류가 발생했습니다: {e}")

        # 누적 레포트 표시
        if st.session_state.interview_records:
            st.markdown("---")
            st.markdown("### 📘 누적 면접 레포트")

            df = pd.DataFrame(
                [
                    {
                        "질문번호": r["question_number"],
                        "질문": r["question"],
                        "논리": r["logic"],
                        "진정성": r["sincerity"],
                        "자신감": r["confidence"],
                        "적합성": r["suitability"],
                    }
                    for r in st.session_state.interview_records
                ]
            )
            st.dataframe(df, use_container_width=True)

            # 상세 JSON 다운로드
            report_json = json.dumps(
                st.session_state.interview_records,
                ensure_ascii=False,
                indent=2,
            )
            st.download_button(
                "📥 전체 면접 레포트(JSON) 다운로드",
                data=report_json,
                file_name="interview_report.json",
                mime="application/json",
            )

    st.markdown("---")
    if st.button("⬅️ 다른 생기부 올리기", use_container_width=True):
        go_to("inter_upload")
