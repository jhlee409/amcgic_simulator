import streamlit as st
import firebase_admin
from firebase_admin import credentials, storage
import os
import tempfile
from datetime import datetime
from pytz import timezone

st.set_page_config(page_title="amcgic_simulator")

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'name' not in st.session_state:
    st.session_state['name'] = ''
if 'position' not in st.session_state:
    st.session_state['position'] = ''

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

# 로그인 상태 확인 및 표시
if st.session_state.get('logged_in', False):
    st.success(f"{st.session_state.get('name', '')}님, 환영합니다. 왼쪽 메뉴에서 원하시는 항목을 선택해주세요.")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['name'] = ''
        st.session_state['position'] = ''
        st.rerun()
else:
    # 사용자 입력
    name = st.text_input("Your Name (예: 홍길동)")
    position = st.selectbox("Select Position", ["", "Staff", "F1", "F2 ", "R3", "Student"])
    password = st.text_input("Password", type="password")

    # 로그인 버튼
    if st.button("Login"):
        if not name.strip():
            st.error("한글 이름을 입력해 주세요")
        elif not position.strip():
            st.error("position을 선택해 주세요")
        elif not password.strip():
            st.error("비밀번호를 입력해 주세요")
        elif password == "3180":
            st.session_state['logged_in'] = True
            st.session_state['name'] = name
            st.session_state['position'] = position
            st.success("로그인 성공!")

            # 로그아웃 버튼
            if "logged_in" in st.session_state and st.session_state['logged_in']:
                if st.sidebar.button("Logout"):
                    st.session_state['logged_in'] = False
                    st.success("로그아웃 되었습니다.")

        else:
            st.error("비밀번호가 틀렸습니다")
