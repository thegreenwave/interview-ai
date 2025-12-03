#메인 진입점 (네비게이션만 담당)
# app.py
import streamlit as st

from pages.presentation import (
    render_presentation_menu,
    render_writer_page,
    render_advisor_page,
    render_analyst_page,
)
from pages.interview import (
    render_interview_upload_page,
    render_interview_practice_page,
)

# 페이지 기본 설정
st.set_page_config(page_title="Spec-trum Pro", page_icon="🎙️", layout="wide")

# ✅ 전역 스타일 주입 (카드, 섹션 타이틀 등)
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem !important;   /* 기본: 약 6rem → 우리가 원하는 만큼만 */
    }
</style>
""", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    /* 전체 레이아웃 여백 조정 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }
    /* 공용 카드 스타일 */
    .spec-card {
        background-color: #020617;
        padding: 1.25rem 1.5rem;
        border-radius: 1rem;
        border: 1px solid #1F2937;
        margin-bottom: 1rem;
    }
    .spec-card-tight {
        background-color: #020617;
        padding: 0.9rem 1rem;
        border-radius: 0.9rem;
        border: 1px solid #1F2937;
        margin-bottom: 0.75rem;
    }
    .spec-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #E5E7EB;
    }
    .spec-subtitle {
        font-size: 0.9rem;
        color: #9CA3AF;
        margin-bottom: 0.4rem;
    }
    .spec-pill {
        display: inline-block;
        padding: 0.15rem 0.7rem;
        border-radius: 999px;
        font-size: 0.75rem;
        border: 1px solid #374151;
        color: #9CA3AF;
        margin-right: 0.3rem;
        margin-top: 0.2rem;
    }
    .spec-badge-success {
        color: #22C55E;
        border-color: #22C55E33;
        background-color: #22C55E0D;
    }
    .spec-badge-warn {
        color: #FACC15;
        border-color: #FACC1533;
        background-color: #FACC150D;
    }
    .spec-badge-danger {
        color: #F97373;
        border-color: #F9737333;
        background-color: #F973730D;
    }
    .spec-section-label {
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #6B7280;
        margin-bottom: 0.3rem;
    }
    .spec-feedback-box {
        background-color: #020617;
        border-radius: 0.9rem;
        border: 1px solid #1F2937;
        padding: 0.9rem 1rem;
        margin-top: 0.5rem;
    }
    .spec-feedback-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #E5E7EB;
        margin-bottom: 0.25rem;
    }
    .spec-feedback-body {
        font-size: 0.85rem;
        color: #D1D5DB;
        line-height: 1.5;
    }
    .spec-question-number {
        font-size: 0.8rem;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .spec-question-text {
        font-size: 1rem;
        color: #F9FAFB;
        margin-top: 0.3rem;
    }
    .spec-timer-ok {
        color: #22C55E;
    }
    .spec-timer-warn {
        color: #F59E0B;
    }
    .spec-timer-danger {
        color: #EF4444;
    }
    .spec-timer-label {
        font-size: 0.8rem;
        color: #9CA3AF;
        margin-bottom: 0.2rem;
    }
    .spec-timer-value {
        font-size: 1.2rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 이하 기존 네비/상태 초기화 부분은 그대로 유지
# ...


# 네비게이션 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = "login"

# 공용 상태 초기화
if "script" not in st.session_state:
    st.session_state.script = ""

if "uni_questions" not in st.session_state:
    st.session_state.uni_questions = ""
if "uni_q_list" not in st.session_state:
    st.session_state.uni_q_list = []
if "current_q_idx" not in st.session_state:
    st.session_state.current_q_idx = 0
if "interview_records" not in st.session_state:
    st.session_state.interview_records = []
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False
if "interview_total_seconds" not in st.session_state:
    st.session_state.interview_total_seconds = 0
if "interview_start_time" not in st.session_state:
    st.session_state.interview_start_time = None


def go_to(page: str):
    st.session_state.step = page
    st.rerun()


# -----------------------------
# 화면 라우팅
# -----------------------------
if st.session_state.step == "login":
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.title("🔒 SPEC-TRUM")
        st.write("역량 전달의 스펙트럼을 넓히다")

        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인", use_container_width=True):
            if pw == "0601":
                st.success("접속 성공!")
                st.session_state.step = "main_menu"
                st.rerun()
            else:
                st.error("비밀번호 오류")

elif st.session_state.step == "main_menu":
    # ===== 상단 히어로 영역 =====
    st.markdown(
        """
        <div class="spec-hero">
            <div>
                <div class="spec-hero-pill">
                    <span>🎙</span>
                    <span>Spec-trum Pro · AI Speech & Interview Coach</span>
                </div>
                <div class="spec-hero-left-title">
                    한 번의 연습도, 실제 면접처럼.
                </div>
                <div class="spec-hero-left-subtitle">
                    발표와 면접을 위한 AI 코칭을 하나의 서비스에서 제공합니다.
                    \n녹음만 하면, 내용·발음·진행 속도까지 자동으로 분석하고
                    질문별 피드백을 누적 레포트로 정리해 드립니다.
                </div>
            </div>
            <div class="spec-hero-right spec-card-tight">
                <div>
                    <div class="spec-mini-metric-label">현재 세션</div>
                    <div class="spec-mini-metric-value">Practice Mode</div>
                    <div class="spec-mini-metric-desc">개인 연습용 비공개 세션입니다.</div>
                </div>
                <div style="margin-top:0.5rem;">
                    <div class="spec-mini-metric-label">추천 시작</div>
                    <div class="spec-mini-metric-value">발표 트랙 → 면접 트랙</div>
                    <div class="spec-mini-metric-desc">먼저 말하기 감각을 익힌 후, 실제 질문으로 연습해 보세요.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ===== 트랙 선택 카드 =====
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div class="spec-card">
                <div class="spec-section-label">Track · Presentation</div>
                <div class="spec-track-card-title">🎤 발표 마스터</div>
                <div class="spec-track-card-sub">
                    발표 대본 생성부터 음성 분석까지, 발표력을 체계적으로 끌어올리고 싶을 때 사용하세요.
                </div>
                <div class="spec-track-bullet">· AI가 주제에 맞는 발표 대본 자동 생성</div>
                <div class="spec-track-bullet">· 대본의 논리 구조·전달력 피드백</div>
                <div class="spec-track-bullet">· 속도·침묵·피치 기반 음성 분석</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        start_pres = st.button("발표 트랙 시작하기", key="go_pres", use_container_width=True)
        if start_pres:
            go_to("pres_menu")

    with col2:
        st.markdown(
            """
            <div class="spec-card">
                <div class="spec-section-label">Track · Interview</div>
                <div class="spec-track-card-title">🎓 생기부 기반 면접</div>
                <div class="spec-track-card-sub">
                    생기부 PDF를 기반으로 실제 면접처럼 질문에 답하고, 질문별 평가를 레포트로 받아볼 수 있습니다.
                </div>
                <div class="spec-track-bullet">· 생기부 내용을 기반으로 한 맞춤형 질문 10개 생성</div>
                <div class="spec-track-bullet">· 총 면접 시간 설정 + 질문별 녹음 & 평가</div>
                <div class="spec-track-bullet">· 논리·진정성·자신감·전공 적합성 레이더 차트</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        start_inter = st.button("면접 트랙 시작하기", key="go_inter", use_container_width=True)
        if start_inter:
            go_to("inter_upload")

    st.markdown("---")

    # ===== 하단 안내(온보딩) =====
    st.markdown(
        """
        <div class="spec-section-label">How to start</div>
        <div class="spec-title" style="font-size:1.0rem;">처음이라면, 이렇게 사용해 보세요</div>
        """,
        unsafe_allow_html=True,
    )

    step_col1, step_col2, step_col3 = st.columns(3)
    with step_col1:
        st.markdown(
            """
            <div class="spec-step-box">
                <strong>1단계 · 발표 감각 익히기</strong><br/>
                간단한 주제를 정하고 발표 트랙에서 대본을 생성한 뒤,
                본인 목소리로 1~2분 발표를 녹음해 보세요.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with step_col2:
        st.markdown(
            """
            <div class="spec-step-box">
                <strong>2단계 · 음성 피드백 확인</strong><br/>
                속도·침묵·피치 변화 그래프를 보면서,
                본인의 말하는 습관을 파악해 보고 개선 포인트를 찾습니다.
            </div>
            """,
            unsafe_allow_html=True,
        )
    with step_col3:
        st.markdown(
            """
            <div class="spec-step-box">
                <strong>3단계 · 실전 면접 시뮬레이션</strong><br/>
                생기부 PDF를 올리고, 실제 면접처럼 질문별로 답변을 녹음해 보세요.
                세션이 끝나면 질문별 점수와 피드백이 정리된 레포트를 받게 됩니다.
            </div>
            """,
            unsafe_allow_html=True,
        )


elif st.session_state.step == "pres_menu":
    render_presentation_menu(go_to)

elif st.session_state.step == "pres_1_writer":
    render_writer_page(go_to)

elif st.session_state.step == "pres_2_advisor":
    render_advisor_page(go_to)

elif st.session_state.step == "pres_3_analyst":
    render_analyst_page(go_to)

elif st.session_state.step == "inter_upload":
    render_interview_upload_page(go_to)

elif st.session_state.step == "inter_practice":
    render_interview_practice_page(go_to)
