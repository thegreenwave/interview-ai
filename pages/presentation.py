#발표 트랙 (대본 작성/평가/분석)
# pages/presentation.py
import streamlit as st
import librosa
import plotly.graph_objects as go

from ai_client import get_client
from analysis_utils import analyze_audio_features, calculate_similarity


client = get_client()


def render_presentation_menu(go_to):
    st.title("🎤 Spec-trum Presentation")
    st.caption("발표 대본 작성부터 음성 분석까지, 한 곳에서 연습해 보세요.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="spec-card">
                <div class="spec-title">📝 대본 작성</div>
                <div class="spec-subtitle">주제만 정하면, AI가 구조화된 발표 대본을 만들어 줍니다.</div>
                <span class="spec-pill">서론-본론-결론</span>
                <span class="spec-pill">3분 발표</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("대본 작성기 실행", use_container_width=True):
            go_to("pres_1_writer")

    with col2:
        st.markdown(
            """
            <div class="spec-card">
                <div class="spec-title">🧐 대본 평가</div>
                <div class="spec-subtitle">작성한 대본을 논리성과 전달력 관점에서 점검해 줍니다.</div>
                <span class="spec-pill">논리 구조</span>
                <span class="spec-pill">강조 포인트</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("대본 평가기 실행", use_container_width=True):
            go_to("pres_2_advisor")

    with col3:
        st.markdown(
            """
            <div class="spec-card">
                <div class="spec-title">📊 음성 분석</div>
                <div class="spec-subtitle">발표 속도, 침묵, 피치 변화까지 실제 발표처럼 분석합니다.</div>
                <span class="spec-pill">Tempo</span>
                <span class="spec-pill">Silence</span>
                <span class="spec-pill">Pitch</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("능력 측정기 실행", use_container_width=True):
            go_to("pres_3_analyst")

    st.markdown("---")
    if st.button("⬅️ 메인 메뉴로 돌아가기", use_container_width=True):
        go_to("main_menu")


def render_writer_page(go_to):
    st.markdown(
        """
        <div class="spec-card">
            <div class="spec-section-label">Presentation · Script</div>
            <div class="spec-title">발표 대본 작성기</div>
            <div class="spec-subtitle">
                발표 주제와 상황을 입력하면, 두괄식 구조의 발표 대본을 자동으로 생성합니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_main, col_side = st.columns([2, 1])

    with col_main:
        topic = st.text_input("발표 주제", placeholder="예: 인공지능의 윤리적 문제")
        context = st.text_input("발표 상황", placeholder="예: 전공 수업 발표, 동아리 발표 등")
        req = st.text_area(
            "요구사항 / 톤",
            placeholder="예: 서론-본론-결론 구조, 3분 분량, 청중 수준은 비전공자",
            height=110,
        )

        if st.button("✨ 대본 생성 (GPT-4o-mini)", type="primary", use_container_width=True):
            if not topic:
                st.warning("발표 주제는 최소한 하나 입력해야 합니다.")
            else:
                with st.spinner("발표 대본을 구성 중입니다..."):
                    prompt = (
                        f"주제: {topic}\n"
                        f"상황: {context}\n"
                        f"요구사항: {req}\n"
                        "위 정보를 바탕으로, 두괄식 구조의 발표 대본을 한국어로 작성해줘. "
                        "서론-본론-결론이 명확히 드러나고, 말로 읽었을 때 자연스러운 문장이어야 한다."
                    )
                    try:
                        res = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": prompt}],
                        )
                        st.session_state.script = res.choices[0].message.content
                        st.success("대본 생성이 완료되었습니다.")
                    except Exception as e:
                        st.error(f"대본 생성 중 오류가 발생했습니다: {e}")

    with col_side:
        st.markdown(
            """
            <div class="spec-card-tight">
                <div class="spec-section-label">Tip</div>
                <div class="spec-subtitle">
                    발표 시간, 청중 수준, 강조하고 싶은 메시지(메시지 1개)를 명확히 적어 줄수록 더 좋은 대본이 나옵니다.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    script = st.session_state.get("script", "")
    if script:
        st.markdown(
            """
            <div class="spec-section-label">Generated Script</div>
            <div class="spec-title">생성된 발표 대본</div>
            """,
            unsafe_allow_html=True,
        )
        st.text_area(
            label="",
            value=script,
            height=300,
        )

    if st.button("⬅️ 발표 메뉴로 복귀", use_container_width=True):
        go_to("pres_menu")


def render_advisor_page(go_to):
    st.markdown(
        """
        <div class="spec-card">
            <div class="spec-section-label">Presentation · Review</div>
            <div class="spec-title">대본 피드백</div>
            <div class="spec-subtitle">
                논리 구조, 전달력, 청중 이해도 관점에서 대본을 점검해 줍니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    default_text = st.session_state.get("script", "")
    user_script = st.text_area(
        "평가받을 발표 대본",
        value=default_text,
        height=220,
        placeholder="여기에 발표 대본을 붙여 넣으세요.",
    )
    user_intent = st.text_input(
        "강조하고 싶은 메시지",
        placeholder="예: AI 윤리의 중요성을 강조하고 싶어요.",
    )

    if st.button("🚀 피드백 받기", type="primary", use_container_width=True):
        if not user_script.strip():
            st.warning("대본을 입력해야 피드백을 제공할 수 있습니다.")
        else:
            with st.spinner("대본을 분석하고 있습니다..."):
                prompt = (
                    f"다음 발표 대본을 평가해줘.\n\n"
                    f"[대본]\n{user_script}\n\n"
                    f"[발표자가 전달하고 싶은 의도]\n{user_intent}\n\n"
                    "- 논리 구조(두괄식인지, 전개가 자연스러운지)\n"
                    "- 핵심 메시지 전달력(청중이 무엇을 기억할지)\n"
                    "- 청중 이해도(전문용어, 난이도 조절)\n"
                    "- 구체적인 개선점(문장 예시 포함)\n"
                    "을 중심으로, 한국어로 친절하게 피드백해줘."
                )
                try:
                    res = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                    )
                    feedback = res.choices[0].message.content

                    st.markdown(
                        """
                        <div class="spec-feedback-box">
                            <div class="spec-feedback-title">AI 코치 피드백</div>
                            <div class="spec-feedback-body">
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown(feedback, unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"피드백 생성 중 오류가 발생했습니다: {e}")

    st.markdown("---")
    if st.button("⬅️ 발표 메뉴로 복귀", use_container_width=True):
        go_to("pres_menu")


def render_analyst_page(go_to):
    st.markdown(
        """
        <div class="spec-card">
            <div class="spec-section-label">Presentation · Voice</div>
            <div class="spec-title">발표 음성 정밀 분석</div>
            <div class="spec-subtitle">
                실제 발표처럼 녹음한 뒤, 발표 속도·침묵·피치·명료도를 한 눈에 확인해 보세요.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ref_text = st.text_area(
        "기준 대본 (선택 사항)",
        value=st.session_state.get("script", ""),
        height=100,
        placeholder="기준이 되는 대본이 있다면 붙여 넣으면 정확도가 계산됩니다.",
    )
    audio = st.audio_input("발표 녹음하기")

    if audio:
        with st.spinner("음성 신호를 분석하고 있습니다..."):
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

                # ===== 상단 메트릭 카드 =====
                col_top1, col_top2, col_top3 = st.columns(3)
                with col_top1:
                    st.metric("발표 시간", f"{tot_dur:.1f}초")
                with col_top2:
                    st.metric("발표 속도 (Tempo)", f"{tempo:.0f} BPM")
                with col_top3:
                    st.metric(
                        "침묵 비율",
                        f"{silence_ratio * 100:.1f}%",
                    )

                col_mid1, col_mid2 = st.columns(2)
                with col_mid1:
                    st.metric("초기 침묵 시간", f"{init_silence:.1f}초")
                with col_mid2:
                    st.metric(
                        "대본과의 일치도",
                        f"{acc:.1f}%" if ref_text.strip() else "N/A",
                    )

                st.markdown("---")

                # ===== 그래프 영역 =====
                st.markdown(
                    """
                    <div class="spec-section-label">Voice Dynamics</div>
                    <div class="spec-title">목소리 변화 분석</div>
                    """,
                    unsafe_allow_html=True,
                )

                col_g1, col_g2 = st.columns(2)

                # 그래프 1: 볼륨 변화
                with col_g1:
                    st.markdown(
                        '<div class="spec-card-tight"><div class="spec-subtitle">RMS 기반 볼륨 변화</div>',
                        unsafe_allow_html=True,
                    )
                    fig_vol = go.Figure()
                    fig_vol.add_trace(
                        go.Scatter(
                            x=times,
                            y=rms,
                            fill="tozeroy",
                            name="Volume",
                        )
                    )
                    fig_vol.update_layout(
                        xaxis_title="시간 (s)",
                        yaxis_title="상대 볼륨 (RMS)",
                        template="plotly_dark",
                        margin=dict(l=40, r=20, t=30, b=30),
                    )
                    st.plotly_chart(fig_vol, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                # 그래프 2: 피치 변화
                with col_g2:
                    st.markdown(
                        '<div class="spec-card-tight"><div class="spec-subtitle">피치(기초 주파수) 변화</div>',
                        unsafe_allow_html=True,
                    )
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
                        template="plotly_dark",
                        margin=dict(l=40, r=20, t=30, b=30),
                    )
                    st.plotly_chart(fig_pitch, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                # 그래프 3: 스펙트럴 센트로이드
                st.markdown(
                    """
                    <div class="spec-card-tight">
                        <div class="spec-subtitle">발음·명료도 경향 (스펙트럴 센트로이드)</div>
                    """,
                    unsafe_allow_html=True,
                )
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
                    template="plotly_dark",
                    margin=dict(l=40, r=20, t=30, b=30),
                )
                st.plotly_chart(fig_cent, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

                # ===== STT 내용 =====
                with st.expander("AI가 인식한 내용 보기 (Whisper STT 결과)"):
                    st.write(transcript)

            except Exception as e:
                st.error(f"오디오 분석 중 오류가 발생했습니다: {e}")

    st.markdown("---")
    if st.button("⬅️ 발표 메뉴로 복귀", use_container_width=True):
        go_to("pres_menu")
