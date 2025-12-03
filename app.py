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
