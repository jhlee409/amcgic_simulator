import streamlit as st
import os
import cv2
import numpy as np
from collections import deque
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.impute import SimpleImputer
from sklearn import svm
from math import atan2, degrees
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, storage
import tempfile

# Set page to wide mode
st.set_page_config(page_title="SHT_training", layout="wide")

# 로그인 상태 확인
if "logged_in" not in st.session_state or not st.session_state['logged_in']:
    st.warning('로그인이 필요합니다.')
    st.stop()

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
    firebase_admin.initialize_app(cred, {"storageBucket": "amcgi-bulletin.appspot.com"})

# 로그아웃 버튼
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()

bucket = storage.bucket('amcgi-bulletin.appspot.com')

st.header("SHT_training")
st.markdown("이 페이지는 EGD simulator을 대상으로 한 SHT training 홈 페이지입니다.")
st.write("---")

st.subheader("SHT 설명 및 시범 동영상")
st.write("SHT 훈련 요령을 설명한 동영상입니다. 마지막에는 전문가의 시범 동영상이 있습니다. 실습전에 예습하세요.")
try:
    bucket = storage.bucket('amcgi-bulletin.appspot.com')
    demonstration_blob = bucket.blob('Simulator_training/SHT/SHT_orientation.mp4')
    if demonstration_blob.exists():
        demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
        
        # 세션 상태 초기화
        if 'show_video' not in st.session_state:
            st.session_state.show_video = False
            
        # 비디오 플레이어를 위한 placeholder 생성
        video_player_placeholder = st.empty()
        
        # 동영상 시청 버튼
        if st.button("동영상 시청"):
            # 비디오 표시 상태 토글
            st.session_state.show_video = not st.session_state.show_video
            
            if st.session_state.show_video:
                # 로그 파일 생성 및 업로드
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                    log_content = f"SHT_orientation video watched by {name} ({position}) on {current_date}"
                    temp_file.write(log_content)
                    temp_file_path = temp_file.name

                # Firebase Storage에 로그 파일 업로드
                log_blob = bucket.blob(f"Simulator_training/SHT/log_SHT/{position}*{name}*SHT")
                log_blob.upload_from_filename(temp_file_path)
                os.unlink(temp_file_path)
            
        # 비디오 플레이어 표시
        if st.session_state.show_video:
            # 동영상 플레이어 렌더링
            with video_player_placeholder.container():
                video_html = f'''
                <div style="display: flex; justify-content: center;">
                    <video width="1000" height="800" controls controlsList="nodownload">
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
    else:
        st.error("SHT 설명 동영상 파일을 찾을 수 없습니다.")

except Exception as e:
    st.error(f"SHT 설명 동영상 파일 재생 중 오류가 발생했습니다: {e}")

st.write("---")

# File upload
uploaded_file = None
st.subheader("SHT 수행 동영상 업로드")
uploaded_file = st.file_uploader("업로드할 SHT 수행 동영상을 선택하세요 (100 MB 이하로 해주세요.):", type=["avi", "mp4"])

if uploaded_file:
    try:
        # Create a temporary directory to store the video file
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save the uploaded file temporarily
            temp_video_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Get current date
            current_date = datetime.now().strftime("%Y-%m-%d")

            # Generate file names
            extension = os.path.splitext(uploaded_file.name)[1]  # Extract file extension
            video_file_name = f"{position}*{name}*SHT_result{extension}"

            # Firebase Storage upload for video
            bucket = storage.bucket('amcgi-bulletin.appspot.com')
            video_blob = bucket.blob(f"Simulator_training/SHT/SHT_result/{video_file_name}")
            video_blob.upload_from_filename(temp_video_path, content_type=uploaded_file.type)

            # Generate log file name
            log_file_name = f"{position}*{name}*SHT_result"

            # Create log file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                log_content = f"SHT_result video uploaded by {name} ({position}) on {current_date}"
                temp_file.write(log_content)
                temp_file_path = temp_file.name

            # Firebase Storage upload for log file
            log_blob = bucket.blob(f"Simulator_training/SHT/log_SHT_result/{log_file_name}")
            log_blob.upload_from_filename(temp_file_path)

            # Remove temporary log file
            os.unlink(temp_file_path)

            # Success message
            st.success(f"{video_file_name} 파일이 성공적으로 업로드되었습니다!")
            st.session_state.show_file_list = True
    except Exception as e:
        # Error message
        st.error(f"업로드 중 오류가 발생했습니다: {e}")