import streamlit as st
from datetime import datetime, timezone
import requests

def check_login():
    """로그인 상태를 확인하고 사용자 정보를 반환합니다."""
    if "logged_in" not in st.session_state or not st.session_state['logged_in']:
        st.warning('로그인이 필요합니다.')
        st.stop()
    return st.session_state['name'], st.session_state['position']

def handle_logout():
    """로그아웃 처리를 수행합니다."""
    if st.sidebar.button("Logout"):
        # 로그아웃 시간과 duration 계산
        logout_time = datetime.now(timezone.utc)
        login_time = st.session_state.get('login_time')
        duration = round((logout_time - login_time).total_seconds() / 60) if login_time else 0

        # 로그아웃 이벤트 기록
        logout_data = {
            "position": st.session_state.get('position'),
            "name": st.session_state.get('name'),
            "time": logout_time.isoformat(),
            "event": "logout",
            "duration": duration
        }
        
        # Supabase에 로그아웃 기록 전송
        supabase_url = st.secrets["supabase_url"]
        supabase_key = st.secrets["supabase_key"]
        supabase_headers = {
            "Content-Type": "application/json",
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}"
        }
        
        requests.post(f"{supabase_url}/rest/v1/login", headers=supabase_headers, json=logout_data)
        
        st.session_state.clear()
        st.success("로그아웃 되었습니다.")
        st.rerun() 