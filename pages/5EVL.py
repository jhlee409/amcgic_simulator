import streamlit as st
import os
import tempfile
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, storage

# Set page to wide mode
st.set_page_config(page_title="EVL_skill_evaluation", layout="wide")

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

    st.header("EVL_skill_evaluation")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.markdown("이 페이지는 EVL simulator을 대상으로 한 EVL 검사 수행에 도움이 되는 자료를 제공하는 페이지입니다.")
        st.markdown("EVL multiband 사용방법 및 demo.mp4 동영상을 다운받아 예습하세요.")
    st.write("---")
   
    st.subheader("EVL multiband 사용방법 및 demo")
    st.write("우리 병원에서는 Cook medical에서 생산되는 6 shooter multiband를  사용하고 있습니다.")
    st.write("이 multiband 사용 방법과 마지막에 expert의 시범 동영상을 예습하세요.")
    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        demonstration_blob = bucket.blob('Simulator_training/EVL/EVL multiband 사용방법 및 demo.mp4')
        if demonstration_blob.exists():
            if st.download_button(
                label="동영상 다운로드",
                data=demonstration_blob.download_as_bytes(),
                file_name="EVL_multiband 사용방법 및 demo.mp4",
                mime="video/mp4",
                key="expert_demo_download"
            ):
                st.success("EVL multiband 사용방법 및 demo 동영상이 다운로드되었습니다.")
                # 로그 파일 생성 및 업로드
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                    log_content = f"EVL_expert_demo video downloaded by {name} ({position}) on {current_date}"
                    temp_file.write(log_content)
                    temp_file_path = temp_file.name

                # Firebase Storage에 로그 파일 업로드
                log_blob = bucket.blob(f"Simulator_training/EVL/log_EVL/{position}*{name}*EVL")
                log_blob.upload_from_filename(temp_file_path)
                os.unlink(temp_file_path)
        else:
            st.error("EVL 시범 동영상 파일을 찾을 수 없습니다.")

    except Exception as e:
        st.error(f"EVL 시범 동영상 파일 다운로드 중 오류가 발생했습니다: {e}")

   
else:
    st.warning('Please log in to read more.')