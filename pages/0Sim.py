import streamlit as st
import os
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, storage
import tempfile
from utils.auth import check_login, handle_logout

# Set page to wide mode
st.set_page_config(page_title="Simulation center", layout="wide")

# 로그인 상태 확인
name, position = check_login()

# 로그아웃 처리
handle_logout()

# Initialize Firebase only if it hasn't been initialized
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
        "client_x509_cert_url": st.secrets["client_x509_cert_url"]
    })
    firebase_admin.initialize_app(cred)

# Title and Instructions
st.title("Simulation Center EGD basic course orientation")
with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
    st.markdown("이 페이지는 Simulation center EGD basic course에 대한 orientation 동영상을 시청하는 곳입니다.")
    st.write("simulation center를 이용하기 전에, simulation_center_orientation.mp4 파일을 시청하세요.")
st.write("---")

# Initialize session state
if 'name_selected' not in st.session_state:
    st.session_state.name_selected = False
if 'show_file_list' not in st.session_state:
    st.session_state.show_file_list = False
if 'download_clicked' not in st.session_state:
    st.session_state.download_clicked = False

# Add download button for EGD procedure document
st.subheader("Simulation Center EGD basic course orientation 파일 시청")
try:
    bucket = storage.bucket('amcgi-bulletin.appspot.com')
    sim_blob = bucket.blob('Simulator_training/sim_orientation/simulation_center_orientation.mp4')
    if sim_blob.exists():
        sim_url = sim_blob.generate_signed_url(expiration=timedelta(minutes=15))
        
        # Initialize session state for video player
        if 'show_video' not in st.session_state:
            st.session_state.show_video = False
        
        # 동영상 시청 버튼
        if st.button("동영상 시청"):
            # 비디오 표시 상태 토글
            st.session_state.show_video = not st.session_state.show_video
            
            if st.session_state.show_video:
                # 로그 파일 생성 및 업로드
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                    log_content = f"Sim_orientation video watched by {name} ({position}) on {current_date}"
                    temp_file.write(log_content)
                    temp_file_path = temp_file.name

                # Firebase Storage에 로그 파일 업로드
                log_blob = bucket.blob(f"Simulator_training/Sim/log_Sim/{position}*{name}*Sim")
                log_blob.upload_from_filename(temp_file_path)
                os.unlink(temp_file_path)
            
        # 비디오 플레이어 표시
        if st.session_state.show_video:
            st.video(sim_url)

    else:
        st.error("simulation center 오리엔테이션 문서를 찾을 수 없습니다.")
    
except Exception as e:
    st.error(f"simulation center 오리엔테이션 파일 로드 중 오류가 발생했습니다.: {e}")
