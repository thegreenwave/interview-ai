#OpenAI 클라이언트
import os
import streamlit as st
from openai import OpenAI


def get_client() -> OpenAI:
    """
    Streamlit secrets 또는 환경변수에서 OPENAI_API_KEY를 읽어
    OpenAI 클라이언트를 리턴한다.
    """
    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    # 환경변수에 이미 세팅되어 있다면 이 줄만으로 충분
    client = OpenAI()
    return client
