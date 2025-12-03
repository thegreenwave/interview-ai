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
