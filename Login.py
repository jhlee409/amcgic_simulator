import streamlit as st
import firebase_admin
from firebase_admin import credentials, storage
import os
import tempfile
from datetime import datetime
from pytz import timezone

st.set_page_config(page_title="amcgic_simulator")


# Streamlit 페이지 설정
st.title("AMC GI 상부 Simulator training")
st.header("Login page")
st.markdown(
    '''
    1. 이 게시판은 서울 아산병원 GI 상부 전용 게시판입니다.
    1. GI 상부의 simulattor training 관련 자료를 제곻하고 결과를 업로드하기 위한 페이지 입니다.
    1. 한글 이름은 게시판에 접속하셨는지 확인하는 자료이므로 반드시 기입해 주세요.
    '''
)
st.divider()

# 사용자 입력

name = st.text_input("Your Name (예: 홍길동)")
position = st.selectbox("Select Position", ["", "Staff", "F1", "F2 ", "R3", "Student"])
password = st.text_input("Password", type="password")

# 입력 검증
show_login_button = True

if not name.strip():
    st.error("한글 이름을 입력해 주세요")
    show_login_button = False
elif not any(0xAC00 <= ord(char) <= 0xD7A3 for char in name):
    st.error("한글 이름을 입력해 주세요")
    show_login_button = False

if not position.strip():
    st.error("position을 선택해 주세요")
    show_login_button = False

if not password.strip():
    st.error("비밀번호를 입력해 주세요")
    show_login_button = False

# 모든 조건이 충족되면 로그인 버튼 표시
if show_login_button:
    if st.button("Login"):
        if password == "3180":
            st.session_state['logged_in'] = True
            st.session_state['name'] = name
            st.session_state['position'] = position
            st.success("로그인 성공!")
            st.rerun()
        else:
            st.error("비밀번호가 틀렸습니다")

# 로그아웃 버튼
if "logged_in" in st.session_state and st.session_state['logged_in']:
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.success("로그아웃 되었습니다.")
