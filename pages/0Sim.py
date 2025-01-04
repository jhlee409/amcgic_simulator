import streamlit as st
import os
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, storage
import tempfile

# Set page to wide mode
st.set_page_config(page_title="Sim", layout="wide")

if "logged_in" in st.session_state and st.session_state['logged_in']:
    # 세션에서 사용자 정보 가져오기
    name = st.session_state['name']
    position = st.session_state['position']

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
    st.write("이 페이지는 Simulation center EGD basic course에 대한 orientation 동영상을 다운 받는 곳입니다.")
    st.write("simulation center를 이용하기 전에, simulation_center_orientation.mp4 파일을 다운 받아 시청하세요.")
    st.write("---")

    # Initialize session state
    if 'name_selected' not in st.session_state:
        st.session_state.name_selected = False
    if 'show_file_list' not in st.session_state:
        st.session_state.show_file_list = False
    if 'download_clicked' not in st.session_state:
        st.session_state.download_clicked = False

    # Add download button for EGD procedure document
    st.subheader("Simulation Center EGD basic course orientation 파일 다운로드")
    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        sim_blob = bucket.blob('Simulator_training/sim_orientation/simulation_center_orientation.mp4')
        if sim_blob.exists():
            sim_url = sim_blob.generate_signed_url(expiration=timedelta(minutes=15))
            if st.download_button(
                label="오리엔테이션 파일 다운로드",
                data=sim_url,
                file_name="simulation_center_orientation.mp4",
                mime="video/mp4",
            ):
                try:
                    # 현재 날짜 가져오기
                    current_date = datetime.now().strftime("%Y-%m-%d")
                    
                    # 로그 파일 이름 생성
                    log_file_name = f"{position}*{name}*sim_orientation"
                    
                    # 임시 파일 생성
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                        log_content = f"Orientation file downloaded by {name} ({position}) on {current_date}"
                        temp_file.write(log_content)
                        temp_file_path = temp_file.name

                    # Firebase Storage에 로그 파일 업로드
                    bucket = storage.bucket('amcgi-bulletin.appspot.com')
                    log_blob = bucket.blob(f"Simulator_training/sim_orientation/log_sim_orientation/{log_file_name}")
                    log_blob.upload_from_filename(temp_file_path)

                    # 임시 파일 삭제
                    os.unlink(temp_file_path)

                    # 성공 메시지 표시
                    st.success(f"오리엔테이션 파일 다운로드 완료 및 로그가 저장되었습니다!")
                    st.session_state.show_file_list = True
                except Exception as e:
                    st.error(f"로그 파일 업로드 중 오류가 발생했습니다: {e}")
        else:
            st.error("simulation center 오리엔테이션 문서를 찾을 수 없습니다.")
    except Exception as e:
        st.error(f"simulation center 오리엔테이션 파일 다운로드 중 오류가 발생했습니다.: {e}")

    st.write("---")

    # 로그아웃 버튼
    if "logged_in" in st.session_state and st.session_state['logged_in']:
        if st.sidebar.button("Logout"):
            st.session_state['logged_in'] = False
            st.success("로그아웃 되었습니다.")

else:
    st.warning('Please log in to read more.')
