# app.py
import streamlit as st
import time
from auth import init_db, create_user, authenticate_user

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
# DB 초기화
init_db()

# ✅ 전역 스타일 주입 (UI 숨김 처리 포함)
st.markdown("""
<style>
    /* [NEW] Streamlit 기본 UI 숨기기 */
    #MainMenu {visibility: hidden;} /* 상단 햄버거 메뉴 숨김 */
    header {visibility: hidden;}    /* 상단 헤더 데코레이션 숨김 */
    footer {visibility: hidden;}    /* 하단 'Made with Streamlit' 푸터 숨김 */
    .stDeployButton {display:none;} /* Deploy 버튼 숨김 */

    /* 전체 레이아웃 여백 조정 */
    .block-container {
        padding-top: 3rem;   /* 헤더를 숨겼으므로 상단 여백을 조금 줄여도 됨 (5rem -> 3rem) */
        padding-bottom: 3rem;
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
    .spec-card-highlight {
        background-color: #172554;
        padding: 1.25rem 1.5rem;
        border-radius: 1rem;
        border: 1px solid #3B82F6;
        margin-bottom: 1rem;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.3);
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
    .spec-price-text {
        font-size: 2rem;
        font-weight: 700;
        color: #F3F4F6;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .spec-price-period {
        font-size: 0.9rem;
        color: #9CA3AF;
        font-weight: 400;
    }
    .spec-section-label {
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #6B7280;
        margin-bottom: 0.3rem;
    }
    .spec-step-box {
        background-color: #111827;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #374151;
        font-size: 0.9rem;
        color: #D1D5DB;
        height: 100%;
    }
    /* 멤버십 배지 스타일 */
    .badge-free {
        background-color: #374151;
        color: #D1D5DB;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        margin-left: 8px;
    }
    .badge-pro {
        background-color: #3B82F6;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-left: 8px;
    }
</style>
""", unsafe_allow_html=True)


# 네비게이션 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = "login"

if "next_dest" not in st.session_state:
    st.session_state.next_dest = "main_menu"

if "user_plan" not in st.session_state:
    st.session_state.user_plan = "free" 

# 공용 상태 초기화
if "script" not in st.session_state:
    st.session_state.script = ""
if "user" not in st.session_state:
    st.session_state.user = None

# 인터뷰 관련 상태
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
        st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
        st.title("🔒 Spec-trum Pro")
        st.caption("개인 계정으로 로그인하여 발표/면접 연습 기록을 분리해서 관리합니다.")

        tab_login, tab_signup = st.tabs(["로그인", "회원가입"])

        # 로그인 탭
        with tab_login:
            login_username = st.text_input("아이디", key="login_username")
            login_password = st.text_input("비밀번호", type="password", key="login_password")

            if st.button("로그인", use_container_width=True, key="login_button"):
                ok, msg = authenticate_user(login_username, login_password)
                if ok:
                    st.success(msg)
                    st.session_state.user = login_username
                    # 로그인 시 기본 플랜 설정
                    if "user_plan" not in st.session_state:
                        st.session_state.user_plan = "free"

                    # 상태 초기화
                    st.session_state.script = ""
                    st.session_state.uni_questions = ""
                    st.session_state.uni_q_list = []
                    st.session_state.current_q_idx = 0
                    st.session_state.interview_records = []
                    st.session_state.interview_started = False

                    st.session_state.step = "main_menu"
                    st.rerun()
                else:
                    st.error(msg)

        # 회원가입 탭
        with tab_signup:
            signup_username = st.text_input("새 아이디", key="signup_username")
            signup_password = st.text_input("새 비밀번호", type="password", key="signup_password")
            signup_password2 = st.text_input("비밀번호 확인", type="password", key="signup_password2")

            if st.button("회원가입", use_container_width=True, key="signup_button"):
                if signup_password != signup_password2:
                    st.error("비밀번호가 서로 일치하지 않습니다.")
                else:
                    ok, msg = create_user(signup_username, signup_password)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)


elif st.session_state.step == "main_menu":
    if st.session_state.user is None:
        st.session_state.step = "login"
        st.rerun()

    # 상단 정보바 구성
    top_bar_col1, top_bar_col2 = st.columns([2, 1])
    
    with top_bar_col1:
        plan_badge = ""
        if st.session_state.user_plan == "pro":
            plan_badge = '<span class="badge-pro">PRO</span>'
        else:
            plan_badge = '<span class="badge-free">FREE</span>'
            
        st.markdown(f"👤 **{st.session_state.user}** 님 {plan_badge}", unsafe_allow_html=True)

    with top_bar_col2:
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("🛒 멤버십 관리", use_container_width=True):
                st.session_state.next_dest = "main_menu"
                go_to("pricing")
        with btn_col2:
            if st.button("로그아웃", use_container_width=True):
                st.session_state.user = None
                st.session_state.step = "login"
                st.rerun()

    # ===== 상단 히어로 영역 =====
    st.markdown(
        """
        <div class="spec-hero">
            <div style="margin-bottom: 2rem;">
                <div style="font-size: 0.9rem; color: #6B7280; margin-bottom: 0.5rem;">🎙 Spec-trum Pro · AI Speech & Interview Coach</div>
                <div style="font-size: 2.2rem; font-weight: 700; color: #F9FAFB; line-height: 1.3;">
                    한 번의 연습도,<br>실제 면접처럼.
                </div>
                <div style="margin-top: 1rem; color: #9CA3AF;">
                    발표와 면접을 위한 AI 코칭을 하나의 서비스에서 제공합니다.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    
    # ===== 트랙 선택 카드 =====
    col1, col2 = st.columns(2)

    with col1:
        pres_desc = "발표 대본 생성부터 음성 분석까지."
        if st.session_state.user_plan == "free":
            pres_desc += " <br><span style='color:#F59E0B; font-size:0.8rem;'>⚠️ Free 플랜: 일 3회 생성 제한</span>"
        else:
            pres_desc += " <br><span style='color:#3B82F6; font-size:0.8rem;'>✨ Pro 플랜: 무제한 생성 가능</span>"

        st.markdown(
            f"""
            <div class="spec-card">
                <div class="spec-section-label">Track · Presentation</div>
                <div class="spec-title">🎤 발표 마스터</div>
                <div class="spec-subtitle">
                    {pres_desc}
                </div>
                <div style="font-size: 0.85rem; color: #6B7280; margin-top: 1rem;">
                    · AI 대본 생성 & 구조 피드백<br>
                    · 속도/침묵/피치 음성 분석<br>
                    · 객관적 AI 평가 리포트
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("발표 트랙 시작하기", key="go_pres", use_container_width=True):
            st.session_state.next_dest = "pres_menu"
            go_to("pres_menu")

    with col2:
        inter_desc = "생기부 PDF 기반 모의면접."
        if st.session_state.user_plan == "free":
            inter_desc += " <br><span style='color:#F59E0B; font-size:0.8rem;'>⚠️ Free 플랜: 상세 레포트 미제공</span>"
        else:
            inter_desc += " <br><span style='color:#3B82F6; font-size:0.8rem;'>✨ Pro 플랜: 상세 분석 레포트 제공</span>"

        st.markdown(
            f"""
            <div class="spec-card">
                <div class="spec-section-label">Track · Interview</div>
                <div class="spec-title">🎓 생기부 기반 면접</div>
                <div class="spec-subtitle">
                    {inter_desc}
                </div>
                <div style="font-size: 0.85rem; color: #6B7280; margin-top: 1rem;">
                    · 생기부 맞춤형 질문 10개 생성<br>
                    · 실전 모의면접 시뮬레이션<br>
                    · 5각형 역량 분석 차트 제공
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("면접 트랙 시작하기", key="go_inter", use_container_width=True):
            st.session_state.next_dest = "inter_upload"
            go_to("inter_upload")

    st.markdown("---")

    # ===== 하단 안내(온보딩) =====
    st.markdown(
        """
        <div class="spec-section-label">How to start</div>
        <div class="spec-title" style="font-size:1.0rem; margin-bottom: 1rem;">처음이라면, 이렇게 사용해 보세요</div>
        """,
        unsafe_allow_html=True,
    )

    step_col1, step_col2, step_col3 = st.columns(3)
    with step_col1:
        st.markdown(
            """
            <div class="spec-step-box">
                <strong style="color:#F3F4F6;">1. 발표 감각 익히기</strong><br/>
                <br/>
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
                <strong style="color:#F3F4F6;">2. 음성 피드백 확인</strong><br/>
                <br/>
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
                <strong style="color:#F3F4F6;">3. 실전 면접 시뮬레이션</strong><br/>
                <br/>
                면접자료를 올리고, 실제 면접같은 모의면접을 진행해 보세요.
                세션 이후 질문별 점수와 피드백 레포트를 받게 됩니다.
            </div>
            """,
            unsafe_allow_html=True,
        )

# [NEW] 요금제 선택 페이지 (상점)
elif st.session_state.step == "pricing":
    if st.session_state.user is None:
        st.warning("로그인 세션이 만료되었습니다.")
        st.session_state.step = "login"
        st.rerun()

    if st.button("← 돌아가기"):
        target = st.session_state.get("next_dest", "main_menu")
        go_to(target)

    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 3rem; margin-top: 1rem;">
            <div class="spec-section-label">Pricing Plan</div>
            <h1 style="color: #F9FAFB; font-size: 2.2rem; font-weight: 700;">멤버십 플랜 변경</h1>
            <p style="color: #9CA3AF;">현재 나의 플랜: <strong style="color:white;">{}</strong></p>
        </div>
        """.format(st.session_state.user_plan.upper()), 
        unsafe_allow_html=True
    )

    p_col1, p_col2, p_col3 = st.columns(3)

    # 1. Basic Plan
    with p_col1:
        is_current = (st.session_state.user_plan == "free")
        border_color = "#22C55E" if is_current else "#1F2937"
        
        st.markdown(
            f"""
            <div class="spec-card" style="height: 100%; border-color: {border_color};">
                <div class="spec-title">🌱 Starter</div>
                <div class="spec-price-text">Free</div>
                <div class="spec-subtitle">기본적인 AI 코칭 체험</div>
                <hr style="border-color: #374151; margin: 1.5rem 0;">
                <div style="color: #D1D5DB; font-size: 0.9rem; line-height: 2;">
                    ✅ 일 3회 대본 생성<br>
                    ✅ 기본 음성 분석 (속도)<br>
                    ✅ 면접 질문 5개 생성<br>
                    ❌ 상세 AI 피드백 리포트
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        if is_current:
            st.button("현재 이용 중", key="plan_basic_active", disabled=True, use_container_width=True)
        else:
            if st.button("Starter로 변경", key="plan_basic", use_container_width=True):
                st.session_state.user_plan = "free"
                st.toast("Starter 플랜으로 변경되었습니다.", icon="✅")
                time.sleep(1)
                st.rerun()

    # 2. Pro Plan
    with p_col2:
        is_current = (st.session_state.user_plan == "pro")
        card_class = "spec-card-highlight" if not is_current else "spec-card"
        style_extra = f"border: 2px solid #22C55E;" if is_current else ""
        
        st.markdown(
            f"""
            <div class="{card_class}" style="height: 100%; position: relative; {style_extra}">
                <div style="position: absolute; top: -12px; right: 20px; background: #3B82F6; color: white; padding: 4px 12px; border-radius: 999px; font-size: 0.75rem; font-weight: 600;">POPULAR</div>
                <div class="spec-title" style="color: #60A5FA;">🚀 Pro</div>
                <div class="spec-price-text">₩ 9,900 <span class="spec-price-period">/ mo</span></div>
                <div class="spec-subtitle">취업 준비와 발표 연습에 최적화</div>
                <hr style="border-color: #3B82F6; margin: 1.5rem 0; opacity: 0.3;">
                <div style="color: #E5E7EB; font-size: 0.9rem; line-height: 2;">
                    ✅ <strong>무제한</strong> 대본 생성<br>
                    ✅ 정밀 음성 분석 (속도/침묵/피치)<br>
                    ✅ 생기부 기반 면접 질문 10개<br>
                    ✅ 상세 AI 피드백 리포트 제공
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        if is_current:
            st.button("현재 이용 중", key="plan_pro_active", disabled=True, use_container_width=True)
        else:
            if st.button("Pro 플랜 구독하기", key="plan_pro", type="primary", use_container_width=True):
                st.balloons()
                st.session_state.user_plan = "pro"
                st.toast("Pro 플랜이 활성화되었습니다!", icon="🚀")
                time.sleep(1.5)
                st.rerun()

    # 3. Enterprise Plan
    with p_col3:
        st.markdown(
            """
            <div class="spec-card" style="height: 100%;">
                <div class="spec-title">🏢 Enterprise</div>
                <div class="spec-price-text">Contact</div>
                <div class="spec-subtitle">학교/단체 교육용 관리자 기능</div>
                <hr style="border-color: #374151; margin: 1.5rem 0;">
                <div style="color: #D1D5DB; font-size: 0.9rem; line-height: 2;">
                    ✅ Pro 기능 전체 포함<br>
                    ✅ 학생 관리 대시보드 제공<br>
                    ✅ 커스텀 평가 기준 설정<br>
                    ✅ 전담 기술 지원
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("문의하기", key="plan_ent", use_container_width=True):
            st.info("관리자에게 문의가 전송되었습니다.")


# -----------------------------
# 기존 기능 페이지 라우팅
# -----------------------------
elif st.session_state.step == "pres_menu":
    if st.session_state.user is None:
        st.warning("로그인 후 이용할 수 있습니다.")
        st.session_state.step = "login"
        st.rerun()
    render_presentation_menu(go_to)

elif st.session_state.step == "pres_1_writer":
    if st.session_state.user is None:
        st.warning("로그인 후 이용할 수 있습니다.")
        st.session_state.step = "login"
        st.rerun()
    render_writer_page(go_to)

elif st.session_state.step == "pres_2_advisor":
    if st.session_state.user is None:
        st.warning("로그인 후 이용할 수 있습니다.")
        st.session_state.step = "login"
        st.rerun()
    render_advisor_page(go_to)

elif st.session_state.step == "pres_3_analyst":
    if st.session_state.user is None:
        st.warning("로그인 후 이용할 수 있습니다.")
        st.session_state.step = "login"
        st.rerun()
    render_analyst_page(go_to)

elif st.session_state.step == "inter_upload":
    if st.session_state.user is None:
        st.warning("로그인 후 이용할 수 있습니다.")
        st.session_state.step = "login"
        st.rerun()
    
    if st.session_state.user_plan == "free":
        st.info("💡 Free 플랜 이용 중: 면접 질문이 5개로 제한되며, 상세 분석 리포트가 간소화됩니다.")
    
    render_interview_upload_page(go_to)

elif st.session_state.step == "inter_practice":
    if st.session_state.user is None:
        st.warning("로그인 후 이용할 수 있습니다.")
        st.session_state.step = "login"
        st.rerun()
    render_interview_practice_page(go_to)
