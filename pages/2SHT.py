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

if "logged_in" in st.session_state and st.session_state['logged_in']:
    # 세션에서 사용자 정보 가져오기
    name = st.session_state['name']
    position = st.session_state['position']

    # 로그아웃 버튼
    if "logged_in" in st.session_state and st.session_state['logged_in']:
        if st.sidebar.button("Logout"):
            st.session_state['logged_in'] = False
            st.success("로그아웃 되었습니다.")

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

    st.header("SHT_training")
    st.markdown("이 페이지는 EGD simulator을 대상으로 한 SHT training 홈 페이지입니다.")
    st.write("---")

    st.subheader("SHT 설명 및 시범 동영상")
    st.write("SHT 훈련 요령을 설명한 동영상입니다. 마지막에는 전문가의 시범 동영상이 있습니다. 실습전에 다운받아서 예습하세요.")
    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        demonstration_blob = bucket.blob('Simulator_training/SHT/SHT_orientation.mp4')
        if demonstration_blob.exists():
            demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
            if st.download_button(
                label="동영상 다운로드",
                data=demonstration_blob.download_as_bytes(),
                file_name="SHT_orientation.mp4",
                mime="video/mp4"
            ):
                st.write("")
        else:
            st.error("SHT 설명 동영상 파일을 찾을 수 없습니다.")

    except Exception as e:
        st.error(f"SHT 설명 동영상 파일 다운로드 중 오류가 발생했습니다: {e}")

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
        
else:
    st.warning('Please log in to read more.')