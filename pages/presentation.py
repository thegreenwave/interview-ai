#발표 트랙 (대본 작성/평가/분석)
# pages/presentation.py
import streamlit as st
import librosa
import plotly.graph_objects as go

from ai_client import get_client
from analysis_utils import analyze_audio_features, calculate_similarity


client = get_client()


def render_presentation_menu(go_to):
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


def render_writer_page(go_to):
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

    if st.session_state.get("script"):
        st.text_area(
            "생성된 대본 (복사해서 쓰세요)",
            st.session_state.script,
            height=300,
        )

    st.markdown("---")
    if st.button("⬅️ 발표 메뉴로 복귀", use_container_width=True):
        go_to("pres_menu")


def render_advisor_page(go_to):
    st.title("🧐 대본 피드백")

    default_text = st.session_state.get("script", "")
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


def render_analyst_page(go_to):
    st.title("📊 발표 능력 정밀 분석")
    st.caption("대본이 있다면 정확도가 측정되고, 없으면 속도와 톤만 분석합니다.")

    ref_text = st.text_area(
        "기준 대본 (선택사항 - 있으면 붙여넣으세요)",
        value=st.session_state.get("script", ""),
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

                # 그래프 3: 스펙트럴 센트로이드
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
