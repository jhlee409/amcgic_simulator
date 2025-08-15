import streamlit as st
import os
import tempfile
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, storage
from utils.auth import check_login, handle_logout

# Set page to wide mode
st.set_page_config(page_title="Injection Simulator Training", layout="wide")

# 로그인 상태 확인
if "logged_in" not in st.session_state or not st.session_state['logged_in']:
    st.warning('로그인이 필요합니다.')
    st.stop()

# 세션에서 사용자 정보 가져오기
name = st.session_state.get('name', '')
position = st.session_state.get('position', '')

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"].replace('\\n', '\n'),
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"],
        "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"],
        "universe_domain": st.secrets["universe_domain"]
    })
    firebase_admin.initialize_app(cred, {"storageBucket": "amcgi-bulletin.appspot.com"})

bucket = storage.bucket('amcgi-bulletin.appspot.com')

# 세션 상태 초기화
if 'show_injection_video' not in st.session_state:
    st.session_state.show_injection_video = False

# Title
st.title("Injection Simulator Training")

st.markdown("---")  # 구분선 추가

st.header("Injection simulator training")
with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
    st.markdown("이 페이지는 Injection simulator을 대상으로 한 Injection 수행에 도움이 되는 자료를 제공하는 페이지입니다.")
    st.write("Injection simulator 실습 전에 'Injection_orientation.mp4' 동영상을 예습하세요.")
st.write("---")

st.subheader("Injection simulator orientation")
try:
    demonstration_blob = bucket.blob('Simulator_training/Injection/Injection_orientation.mp4')
    if demonstration_blob.exists():
        demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
        
        if st.button("동영상 시청", key="injection_video"):
            st.session_state.show_injection_video = not st.session_state.show_injection_video
            
            if st.session_state.show_injection_video:
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                    log_content = f"Injection_orientation video watched by {name} ({position}) on {current_date}"
                    temp_file.write(log_content)
                    temp_file_path = temp_file.name

                log_blob = bucket.blob(f"log/{position}*{name}*Injection")
                log_blob.upload_from_filename(temp_file_path)
                os.unlink(temp_file_path)
        
        if st.session_state.show_injection_video:
            video_html = f'''
            <div style="display: flex; justify-content: center;">
                <video width="1300" controls controlsList="nodownload">
                    <source src="{demonstration_url}" type="video/mp4">
                </video>
            </div>
            <script>
            var video_player = document.querySelector("video");
            video_player.addEventListener('contextmenu', function(e) {{
                e.preventDefault();
            }});
            </script>
            '''
            st.markdown(video_html, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Injection orientation 동영상 파일 재생 중 오류가 발생했습니다: {e}")
