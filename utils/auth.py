import streamlit as st

def check_login():
    """로그인 상태 및 필수 세션 데이터 확인"""
    required_keys = ['logged_in', 'name', 'position']
    if not all(key in st.session_state for key in required_keys) or not st.session_state['logged_in']:
        st.warning('로그인이 필요합니다.')
        st.stop()
    return st.session_state['name'], st.session_state['position']

def handle_logout():
    """로그아웃 처리"""
    if st.sidebar.button("Logout"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun() 