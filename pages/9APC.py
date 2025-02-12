import streamlit as st
import os
import tempfile
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, storage

# Set page to wide mode
st.set_page_config(page_title="APC simulator training", layout="wide")

if "logged_in" in st.session_state and st.session_state['logged_in']:
    # 세션에서 사용자 정보 가져오기
    name = st.session_state['name']
    position = st.session_state['position']

    # 로그아웃 버튼
    if st.sidebar.button("Logout", key="logout_button"):
        st.session_state['logged_in'] = False
        st.success("로그아웃 되었습니다.")
        st.stop()

    def initialize_firebase():
        """Firebase 초기화 함수"""
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
        return storage.bucket('amcgi-bulletin.appspot.com')

    bucket = initialize_firebase()

    st.header("APC simulator training")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.markdown("이 페이지는 APC simulator을 대상으로 한 APC 수행에 도움이 되는 자료를 제공하는 페이지입니다.")
        st.write("APC simulator 실습 전에 'APC_orientation.mp4' 동영상을 예습하세요.")
    st.write("---")
   
    st.subheader("APC simulator orientation")

    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        demonstration_blob = bucket.blob('Simulator_training/APC/APC_orientation.mp4')
        if demonstration_blob.exists():
            # 세션 상태 초기화
            if 'show_video' not in st.session_state:
                st.session_state.show_video = False
            
            # 동영상 시청 버튼
            if st.button(
                label="동영상 시청",
                key="watch_video"
            ):
                # 비디오 표시 상태 토글
                st.session_state.show_video = not st.session_state.show_video
                
                if st.session_state.show_video:
                    # 로그 파일 생성 및 업로드
                    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                        log_content = f"APC_orientation video watched by {name} ({position}) on {current_date}"
                        temp_file.write(log_content)
                        temp_file_path = temp_file.name

                    # Firebase Storage에 로그 파일 업로드
                    log_blob = bucket.blob(f"Simulator_training/APC/log_APC/{position}*{name}*APC")
                    log_blob.upload_from_filename(temp_file_path)
                    os.unlink(temp_file_path)
                
            # 비디오 데이터를 바이트로 가져오기
            video_data = demonstration_blob.download_as_bytes()
            
            # 비디오 플레이어 표시
            if st.session_state.show_video:
                st.video(video_data)
                
                st.success("APC simulator orientation 동영상이 로드되었습니다.")
        else:
            st.error("APC simulator orientation 시범 동영상 파일을 찾을 수 없습니다.")

    except Exception as e:
        st.error(f"APC simulator orientation 동영상 파일 로드 중 오류가 발생했습니다: {e}")

   
else:
    st.warning('Please log in to read more.')