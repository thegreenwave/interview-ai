#면접 트랙 (질문 생성 + 실전 모드)
# pages/interview.py
import time
import json

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from ai_client import get_client
from pdf_utils import extract_text_from_pdf


client = get_client()


def text_to_speech_bytes(text: str) -> bytes:
    """
    OpenAI Audio TTS를 사용해 질문을 음성으로 변환하고,
    MP3 바이트를 반환한다.
    ⚠️ 사용 중인 openai-python SDK 버전에 따라 model 이름이나 속성이 다를 수 있음.
       필요하면 공식 문서를 보고 model/필드를 조정해야 함.
    """
    try:
        # SDK 버전에 맞게 model 이름 수정 필요할 수 있음.
        response = client.audio.speech.create(
            model="gpt-4o-mini-tts",  # 예시: "tts-1" 등으로 교체 가능
            voice="alloy",
            input=text,
        )
        audio_bytes = response.read()
        return audio_bytes
    except Exception as e:
        st.warning(f"TTS 생성 중 오류가 발생했습니다: {e}")
        return b""


def render_interview_upload_page(go_to):
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
                        st.session_state.interview_records = []
                        st.session_state.interview_started = False
                        st.session_state.interview_start_time = None
                        st.session_state.interview_total_seconds = 0

                        go_to("inter_practice")
                    except Exception as e:
                        st.error(f"질문 생성 중 오류가 발생했습니다: {e}")
                else:
                    st.error("텍스트 인식 실패. 이미지 PDF일 가능성이 높습니다. 스캔 품질을 확인해 주세요.")

    st.markdown("---")
    if st.button("⬅️ 메인 메뉴로", use_container_width=True):
        go_to("main_menu")


def render_interview_practice_page(go_to):
    st.title("🎙️ 실전 면접 트레이닝")

    questions_text = st.session_state.get(
        "uni_questions", "아직 생성된 질문이 없습니다. 이전 단계에서 생기부를 업로드해 주세요."
    )
    q_list = st.session_state.get("uni_q_list", [])

    with st.expander("📄 AI가 생성한 전체 질문 원문 보기", expanded=False):
        st.write(questions_text)

    st.markdown("---")

    if not q_list:
        st.warning("질문 리스트를 찾을 수 없습니다. 이전 단계에서 다시 질문을 생성해 주세요.")
    else:
        # 1) 면접 설정 단계
        if not st.session_state.get("interview_started", False):
            st.subheader("⏱ 실전 면접 설정")

            st.write(f"총 질문 수: **{len(q_list)}개**")
            total_minutes = st.slider(
                "총 면접 시간(분) 설정",
                min_value=3,
                max_value=30,
                value=10,
                step=1,
                help="실제 면접처럼 전체 세션 시간을 설정합니다.",
            )

            if st.button("🎬 실전 면접 시작", type="primary"):
                st.session_state.interview_total_seconds = total_minutes * 60
                st.session_state.interview_start_time = time.time()
                st.session_state.interview_started = True
                st.session_state.current_q_idx = 0
                st.session_state.interview_records = []
                st.rerun()

        else:
            # 2) 진행 중인 면접 세션
            total_sec = st.session_state.get("interview_total_seconds", 0)
            start_time = st.session_state.get("interview_start_time", None)

            elapsed = time.time() - start_time if start_time else 0
            remaining = max(0, total_sec - elapsed)

            # 남은 시간 표시
            min_rem = int(remaining // 60)
            sec_rem = int(remaining % 60)

            col_time, col_info = st.columns([1, 2])
            with col_time:
                st.metric(
                    "남은 총 면접 시간",
                    f"{min_rem:02d}:{sec_rem:02d}",
                )
            with col_info:
                st.caption(
                    "※ 남은 시간은 참고용입니다. 실제 답변 녹음 길이는 강제 제한하지 않습니다."
                )

            st.markdown("---")

            # 모든 질문 완료 시
            if st.session_state.current_q_idx >= len(q_list):
                st.success("✅ 모든 질문에 대한 평가가 완료되었습니다.")

                if st.session_state.interview_records:
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

                if st.button("🔁 같은 질문 세트로 다시 면접 보기", use_container_width=True):
                    st.session_state.interview_started = False
                    st.session_state.interview_start_time = None
                    st.session_state.interview_total_seconds = 0
                    st.session_state.current_q_idx = 0
                    st.session_state.interview_records = []
                    st.rerun()

            else:
                # 현재 질문
                idx = st.session_state.current_q_idx
                current_q_number = idx + 1
                current_question = q_list[idx]

                st.subheader(f"질문 {current_q_number} / {len(q_list)}")
                st.write(current_question)

                # 질문을 음성으로 듣고 싶으면 이 버튼 사용 (옵션)
                if st.button("🔊 질문 음성으로 듣기"):
                    audio_bytes = text_to_speech_bytes(current_question)
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3")

                st.markdown("#### 🎤 이 질문에 대한 답변 녹음")
                audio = st.audio_input("질문에 대한 답변을 녹음하세요")

                if st.button("🧠 이 질문 평가하고 다음 질문으로 넘어가기", type="primary"):
                    if audio is None:
                        st.warning("먼저 답변을 녹음해 주세요.")
                    else:
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

                                st.subheader("이번 질문에 대한 평가 리포트")
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

                                # 기록 저장
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

                                # 다음 질문으로 이동
                                st.session_state.current_q_idx += 1
                                st.rerun()

                            except Exception as e:
                                st.error(f"면접 평가 중 오류가 발생했습니다: {e}")

    st.markdown("---")
    if st.button("⬅️ 다른 생기부 올리기", use_container_width=True):
        st.session_state.interview_started = False
        st.session_state.interview_start_time = None
        st.session_state.interview_total_seconds = 0
        st.session_state.current_q_idx = 0
        st.session_state.interview_records = []
        go_to("inter_upload")
