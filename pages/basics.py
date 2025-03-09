import streamlit as st
import os
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, storage
import tempfile
from utils.auth import check_login, handle_logout
import numpy as np
from PIL import Image, ImageDraw, ImageFont
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
import wave
import requests

# Set page to wide mode
st.set_page_config(page_title="Simulator basic training", layout="wide")

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
    # Firebase가 이미 초기화되어 있는지 확인
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {"storageBucket": "amcgi-bulletin.appspot.com"})

# 로그인 상태 확인
if "logged_in" not in st.session_state or not st.session_state['logged_in']:
    st.warning('로그인이 필요합니다.')
    st.stop()

# 세션에서 사용자 정보 가져오기
name = st.session_state.get('name', '')
position = st.session_state.get('position', '')

# 세션 상태 초기화 (페이지 시작 시)
if 'show_sim_video' not in st.session_state:
    st.session_state.show_sim_video = False
if 'show_mt_video' not in st.session_state:
    st.session_state.show_mt_video = False
if 'show_sht_video' not in st.session_state:
    st.session_state.show_sht_video = False
if 'show_emt_video' not in st.session_state:
    st.session_state.show_emt_video = False

# 사이드바에 드롭다운 메뉴와 로그아웃 버튼 배치
selected_option = st.sidebar.selectbox(
    "세부항목 선택",
    ["Sim orientation", "MT", "SHT", "EMT"]
)

st.sidebar.markdown("---")  # 구분선 추가

# 로그아웃 버튼
if "logged_in" in st.session_state and st.session_state['logged_in']:
    if st.sidebar.button("Logout"):
        try:
            # 현재 시간 가져오기
            logout_time = datetime.now(timezone.utc)
            current_time = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            
            # Firebase Storage에서 로그인 로그 가져오기
            bucket = storage.bucket()
            login_blobs = list(bucket.list_blobs(prefix='log_login/'))
            logout_blobs = list(bucket.list_blobs(prefix='log_logout/'))
            
            if login_blobs:
                # 가장 최근 로그인 시간 찾기
                latest_login_blob = max(login_blobs, key=lambda x: x.name)
                login_time_str = latest_login_blob.name.split('/')[-1]
                # UTC 시간으로 파싱하여 시간대 정보 추가
                login_time = datetime.strptime(login_time_str, "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
                
                # 시간 차이 계산 (초 단위)
                time_duration = int((logout_time - login_time).total_seconds())
                
                # 사용자 정보 가져오기
                name = st.session_state.get('name', '이름 없음')
                position = st.session_state.get('position', '직책 미지정')
                
                # duration 로그 저장
                duration_filename = f"{position}*{name}*{time_duration}*{current_time}"
                
                # 임시 파일 생성
                with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
                    temp_file.write(f"Position: {position}\n")
                    temp_file.write(f"Name: {name}\n")
                    temp_file.write(f"Duration (seconds): {time_duration}\n")
                    temp_file.write(f"Logout Time: {current_time}\n")
                    temp_file_path = temp_file.name
                
                # Firebase Storage에 duration 로그 업로드
                duration_blob = bucket.blob(f"log_duration/{duration_filename}")
                duration_blob.upload_from_filename(temp_file_path)
                
                # 임시 파일 삭제
                os.unlink(temp_file_path)
                
                # login과 logout 폴더의 모든 파일 삭제
                for blob in login_blobs:
                    blob.delete()
                for blob in logout_blobs:
                    blob.delete()
                
                # 폴더 자체 삭제
                login_folder = bucket.blob('log_login/')
                logout_folder = bucket.blob('log_logout/')
                if login_folder.exists():
                    login_folder.delete()
                if logout_folder.exists():
                    logout_folder.delete()

                # Supabase에 로그아웃 기록 전송
                logout_data = {
                    "position": position,
                    "name": name,
                    "time": logout_time.isoformat(),
                    "event": "logout",
                    "duration": time_duration
                }
                
                # Supabase 로그아웃 기록
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
                
            else:
                st.error("로그인 기록을 찾을 수 없습니다.")
                
        except Exception as e:
            st.error(f"로그아웃 처리 중 오류가 발생했습니다: {str(e)}")

# 선택된 옵션이 변경될 때 모든 비디오 플레이어 숨기기
if 'previous_selection' not in st.session_state:
    st.session_state.previous_selection = selected_option
elif st.session_state.previous_selection != selected_option:
    st.session_state.show_sim_video = False
    st.session_state.show_mt_video = False
    st.session_state.show_sht_video = False
    st.session_state.show_emt_video = False
    st.session_state.previous_selection = selected_option

# Title and Instructions in main area
st.title("Simulaor training basic course orientation")
with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
    st.markdown("이 페이지는 GI 상부의 simulattor training basic course 관련 자료를 제곻하고 결과를 업로드하기 위한 페이지 입니다.")
    st.markdown("끝낼 때는 반드시 로그아웃 버튼을 눌러 종결하세요. 그냥 종결하면 출석체크가 안됩니다.")
    
st.markdown("---")

# 선택된 옵션에 따라 다른 기능 실행
if selected_option == "Sim orientation":
    st.subheader("Simulation Center EGD basic course orientation 파일 시청")
    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        sim_blob = bucket.blob('Simulator_training/Sim/simulation_center_orientation.mp4')
        if sim_blob.exists():
            sim_url = sim_blob.generate_signed_url(expiration=timedelta(minutes=15))
            
            # 동영상 시청 버튼
            if st.button("동영상 시청"):
                st.session_state.show_sim_video = not st.session_state.show_sim_video
                
                if st.session_state.show_sim_video:
                    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                        log_content = f"Sim_orientation video watched by {name} ({position}) on {current_date}"
                        temp_file.write(log_content)
                        temp_file_path = temp_file.name

                    log_blob = bucket.blob(f"Simulator_training/Sim/log_Sim/{position}*{name}*Sim")
                    log_blob.upload_from_filename(temp_file_path)
                    os.unlink(temp_file_path)
            
            # 비디오 플레이어 표시
            if st.session_state.show_sim_video:
                video_html = f'''
                <div style="display: flex; justify-content: center;">
                    <video width="1300" controls controlsList="nodownload">
                        <source src="{sim_url}" type="video/mp4">
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
            st.error("simulation center 오리엔테이션 문서를 찾을 수 없습니다.")
    except Exception as e:
        st.error(f"simulation center 오리엔테이션 파일 로드 중 오류가 발생했습니다.: {e}")

elif selected_option == "MT":
    # MT 관련 코드
    st.title("MT (Memory Training)")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.markdown("업로드된 동영상은 AI로 평가됩니다. EGD 시행 동작 순서 파일 내용 중 암기해야 하는 내용의 80%이상 암기한 것으로 평가되면 통과입니다.")
        st.markdown("80% 미만인 선생에게는 개별적으로 연락을 할 것이고, 좀 더 훈련해서 재도전 해야 합니다.")
    
    # Add download button for EGD procedure document
    st.subheader("EGD 시행 동작 순서 파일")
    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        method_blob = bucket.blob('Simulator_training/MT/EGD 시행 동작 순서 Bx 포함 2024.docx')
        if method_blob.exists():
            method_url = method_blob.generate_signed_url(expiration=timedelta(minutes=15))
            if st.download_button(
                label="EGD 시행 순서 다운로드",
                data=method_blob.download_as_bytes(),
                file_name="EGD 시행 동작 순서 Bx 포함 2024.docx",
                mime="application/msword",
            ):
                st.write("")
        else:
            st.error("검사과정설명 문서를 찾을 수 없습니다..")
    except Exception as e:
        st.error(f"검사과정설명 문서 파일 다운로드 중 오류가 발생했습니다.: {e}")

    # Add narration download button
    st.write("---")
    st.subheader("나레이션 mp3 다운로드")
    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        narration_blob = bucket.blob('Simulator_training/MT/memory test narration 13분.mp3')
        if narration_blob.exists():
            narration_url = narration_blob.generate_signed_url(expiration=timedelta(minutes=15))
            if st.download_button(
                label="나레이션 mp3 다운로드",
                data=narration_blob.download_as_bytes(),
                file_name="memory_test_narration.mp3",
                mime="audio/mpeg"
            ):
                st.write("")
        else:
            st.error("나레이션 파일을 찾을 수 없습니다.")
    except Exception as e:
        st.error(f"나레이션 파일 다운로드 중 오류가 발생했습니다: {e}")

    st.write("---")

    st.subheader("MT demo 동영상 시청")
    st.markdown("한 피교육자가 제출한 인공지능 분석 99점인 암기 구술 동영상입니다. 합격 기준은 80점 이상입니다.")
    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        demonstration_blob = bucket.blob('Simulator_training/MT/MT_demo.mp4')
        if demonstration_blob.exists():
            demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
            
            # 동영상 시청 버튼
            if st.button("동영상 시청"):
                st.session_state.show_sht_video = not st.session_state.show_sht_video
            
            # 비디오 플레이어 표시
            if st.session_state.show_sht_video:
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
        else:
            st.error("MT demo 동영상 파일을 찾을 수 없습니다.")

    except Exception as e:
        st.error(f"MT demo 동영상 파일 재생 중 오류가 발생했습니다: {e}")

    st.write("---")
    
    # File uploader
    uploaded_file = None
    st.subheader("암기 영상 업로드")
    uploaded_file = st.file_uploader("업로드할 암기 동영상(mp4)을 선택하세요 (100 MB 이하로 해주세요.):", type=["mp4"])

    if uploaded_file:
        try:
            # Create a temporary directory to store the video file
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save the uploaded file temporarily
                temp_video_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_video_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Get current date
                current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

                # Generate file names
                extension = os.path.splitext(uploaded_file.name)[1]  # Extract file extension
                video_file_name = f"{position}*{name}*MT_result{extension}"

                # Firebase Storage upload for video
                bucket = storage.bucket('amcgi-bulletin.appspot.com')
                video_blob = bucket.blob(f"Simulator_training/MT/MT_result/{video_file_name}")
                video_blob.upload_from_filename(temp_video_path, content_type=uploaded_file.type)

                # Generate log file name
                log_file_name = f"{position}*{name}*MT"

                # Create log file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                    log_content = f"MT_result video uploaded by {name} ({position}) on {current_date}"
                    temp_file.write(log_content)
                    temp_file_path = temp_file.name

                # Firebase Storage upload for log file
                log_blob = bucket.blob(f"Simulator_training/MT/log_MT/{log_file_name}")
                log_blob.upload_from_filename(temp_file_path)

                # Remove temporary log file
                os.unlink(temp_file_path)

                # Success message
                st.success(f"{video_file_name} 파일이 성공적으로 업로드되었습니다!")
        except Exception as e:
            # Error message
            st.error(f"업로드 중 오류가 발생했습니다: {e}")

elif selected_option == "SHT":
    st.subheader("SHT (Scope Handling Training) orientation 동영상 시청")
    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        demonstration_blob = bucket.blob('Simulator_training/SHT/SHT_orientation.mp4')
        if demonstration_blob.exists():
            demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
            
            # 동영상 시청 버튼
            if st.button("동영상 시청", key="sht_orientation_video_button"):
                if "show_sht_orientation_video" not in st.session_state:
                    st.session_state.show_sht_orientation_video = True
                else:
                    st.session_state.show_sht_orientation_video = not st.session_state.show_sht_orientation_video
            
            # 비디오 플레이어 표시
            if "show_sht_orientation_video" not in st.session_state:
                st.session_state.show_sht_orientation_video = False
                
            if st.session_state.show_sht_orientation_video:
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
        else:
            st.error("SHT 설명 동영상 파일을 찾을 수 없습니다.")

    except Exception as e:
        st.error(f"SHT 설명 동영상 파일 재생 중 오류가 발생했습니다: {e}")

    st.write("---")

    st.subheader("SHT expert demo 동영상 시청")
    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        demonstration_blob = bucket.blob('Simulator_training/SHT/SHT_expert_demo.mp4')
        if demonstration_blob.exists():
            demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
            
            # 동영상 시청 버튼
            if st.button("동영상 시청", key="sht_expert_demo_video_button"):
                if "show_sht_expert_demo_video" not in st.session_state:
                    st.session_state.show_sht_expert_demo_video = True
                else:
                    st.session_state.show_sht_expert_demo_video = not st.session_state.show_sht_expert_demo_video
            
            # 비디오 플레이어 표시
            if "show_sht_expert_demo_video" not in st.session_state:
                st.session_state.show_sht_expert_demo_video = False
                
            if st.session_state.show_sht_expert_demo_video:
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
        else:
            st.error("SHT expert demo 동영상상 파일을 찾을 수 없습니다.")

    except Exception as e:
        st.error(f"SHT expert demo 동영상 파일 재생 중 오류가 발생했습니다: {e}")

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
                current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

                # Generate file names
                extension = os.path.splitext(uploaded_file.name)[1]  # Extract file extension
                video_file_name = f"{position}*{name}*SHT_result{extension}"

                # Firebase Storage upload for video
                bucket = storage.bucket('amcgi-bulletin.appspot.com')
                video_blob = bucket.blob(f"Simulator_training/SHT/SHT_result/{video_file_name}")
                video_blob.upload_from_filename(temp_video_path, content_type=uploaded_file.type)

                # Generate log file name
                log_file_name = f"{position}*{name}*SHT"

                # Create log file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                    log_content = f"SHT_result video uploaded by {name} ({position}) on {current_date}"
                    temp_file.write(log_content)
                    temp_file_path = temp_file.name

                # Firebase Storage upload for log file
                log_blob = bucket.blob(f"Simulator_training/SHT/log_SHT/{log_file_name}")
                log_blob.upload_from_filename(temp_file_path)

                # Remove temporary log file
                os.unlink(temp_file_path)

                # Success message
                st.success(f"{video_file_name} 파일이 성공적으로 업로드되었습니다!")
        except Exception as e:
            # Error message
            st.error(f"업로드 중 오류가 발생했습니다: {e}")

elif selected_option == "EMT":
    st.subheader("EMT (EGD Method Training) orientation 동영상 시청")
    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        demonstration_blob = bucket.blob('Simulator_training/EMT/EMT_orientation.mp4')
        if demonstration_blob.exists():
            demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
            
            # 동영상 시청 버튼
            if st.button("동영상 시청", key="toggle_video"):
                st.session_state.show_emt_video = not st.session_state.show_emt_video
                
                if st.session_state.show_emt_video:
                    pass  # 로그 파일 전송을 제거하여 버튼 클릭 시 로그가 기록되지 않도록 수정
            
            # 비디오 플레이어 표시
            if st.session_state.show_emt_video:
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
        else:
            st.error("EMT_orientation 동영상 파일을 찾을 수 없습니다.")

    except Exception as e:
        st.error(f"EMT_orientation 동영상 재생 중 오류가 발생했습니다: {e}")

    st.write("---")

    st.subheader("전문가 시범 동영상")
    st.write("전문가가 수행한 EMT 시범 동영상입니다. 잘보고 어떤 점에서 초심자와 차이가 나는지 연구해 보세요.")
    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        demonstration_blob = bucket.blob('Simulator_training/EMT/EMT_expert_demo.mp4')
        if demonstration_blob.exists():
            demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
            
            # 동영상 시청 버튼
            if st.button("동영상 시청", key="toggle_expert_video"):
                st.session_state.show_expert_video = not st.session_state.get('show_expert_video', False)
            
            # 비디오 플레이어 표시
            if st.session_state.get('show_expert_video', False):
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
        else:
            st.error("EMT 시범 동영상 파일을 찾을 수 없습니다.")

    except Exception as e:
        st.error(f"EMT 시범 동영상 파일 로드 중 오류가 발생했습니다: {e}")

    st.write("---")
    
   
    st.subheader("수행 동영상 및 이미지 파일 업로드, 분석 및 최종 평가서 전송")

    uploaded_files = st.file_uploader("분석할 파일들(avi, mp4, bmp)을 탐색기에서 찾아 모두 선택해주세요 단 동영상은 한개만 선택할 수 있습니다.", 
                                    accept_multiple_files=True,
                                    type=['avi', 'bmp', 'mp4'])

    # 파일의 업로드 및 파악
    if uploaded_files:
        st.write(f"총 {len(uploaded_files)}개의 파일이 선택되었습니다.")
        if not name:
            st.error("이름이 입력되지 않았습니다.")
        else:
            # 임시 디렉토리 생성
            temp_dir = "temp_files"
            os.makedirs(temp_dir, exist_ok=True)

            # 파일 분류
            has_bmp = False
            avi_files = []
            bmp_files = []

            # 업로드된 파일 저장 및 분류
            total_files = len(uploaded_files)
            for uploaded_file in uploaded_files:
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                if uploaded_file.name.endswith('.avi') or uploaded_file.name.endswith('.mp4'):
                    avi_files.append(temp_path)
                elif uploaded_file.name.endswith('.bmp'):
                    has_bmp = True
                    bmp_files.append(temp_path)

            st.write(f"avi 파일 수 : {len([file for file in avi_files if file.endswith('.avi')])} , MP4 파일 수 : {len([file for file in avi_files if file.endswith('.mp4')])} , BMP 파일 수: {len(bmp_files)}")

            # 동영상 길이 확인 변수 초기화
            is_video_length_valid = True
            video_duration = 0
            video_file_path = None
            
            # AVI 파일 처리
            total_avi_files = len(avi_files)
            for file_path in avi_files:
                video_file_path = file_path  # 동영상 파일 경로 저장
                camera = cv2.VideoCapture(file_path)
                if not camera.isOpened():
                    st.error("동영상 파일을 열 수 없습니다.")
                    continue

                length = int(camera.get(cv2.CAP_PROP_FRAME_COUNT))
                frame_rate = camera.get(cv2.CAP_PROP_FPS)
                duration = length / frame_rate
                video_duration = duration  # 동영상 길이 저장

                st.write(f"---\n동영상 길이: {int(duration // 60)} 분 {int(duration % 60)} 초")
                if not (300 <= duration <= 330):
                    st.error("동영상의 길이가 5분에서 5분30초를 벗어납니다. 다시 시도해 주세요")
                    is_video_length_valid = False
                else:
                    is_video_length_valid = True

                # BMP 이미지 수 확인
                if not (62 <= len(bmp_files) <= 66):
                    st.error("사진의 숫자가 62장에서 66장 범위를 벗어납니다. 다시 시도해 주세요")
                    is_photo_count_valid = False
                else:
                    is_photo_count_valid = True

                # 동영상 길이와 BMP 파일 수가 모두 유효한 경우에만 분석 진행
                if is_video_length_valid and is_photo_count_valid:
                    st.write(f"비디오 정보 : 총 프레임 수 = {length} , 프레임 레이트 = {frame_rate:.2f}")
                    progress_container = st.empty()
                    progress_container.progress(0)

                    try:
                        # 프레임 처리를 위한 변수 초기화
                        pts = []
                        angle_g = np.array([])
                        distance_g = np.array([])
                        frame_count = 0

                        # 진행률 표시를 위한 컨테이너 생성
                        progress_bar = st.progress(0)
                        progress_text = st.empty()

                        while True:
                            ret, frame = camera.read()
                            if not ret:
                                break

                            # 프레임 카운트 증가
                            frame_count += 1

                            try:
                                # 프레임 분석
                                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                                
                                # 색상 범위 설정 및 마스크 생성
                                green_lower = np.array([40, 40, 40], np.uint8)
                                green_upper = np.array([80, 255, 255], np.uint8)
                                green = cv2.inRange(hsv, green_lower, green_upper)
                                
                                # 노이즈 제거를 위한 모폴로지 연산
                                kernel = np.ones((5, 5), np.uint8)
                                green = cv2.morphologyEx(green, cv2.MORPH_OPEN, kernel)
                                green = cv2.morphologyEx(green, cv2.MORPH_CLOSE, kernel)

                                # 윤곽선 검출
                                contours, hierarchy = cv2.findContours(green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                                
                                # 크기가 200-8000 픽셀 사이인 윤곽선만 필터링
                                filtered_contours = []
                                for contour in contours:
                                    area = cv2.contourArea(contour)
                                    if 200 <= area <= 8000:  # 200-8000 픽셀 사이의 물체만 인식
                                        filtered_contours.append(contour)
                                
                                if len(filtered_contours) > 0:
                                    # 가장 큰 윤곽선 찾기
                                    c = max(filtered_contours, key=cv2.contourArea)
                                    ga = cv2.contourArea(c)
                                    
                                    u = c
                                    pts.extend([frame_count, 2])

                                    # 중심점 계산
                                    M = cv2.moments(u)
                                    if M["m00"] != 0:
                                        px = abs(int(M["m10"] / M["m00"]))
                                        py = abs(int(M["m01"] / M["m00"]))
                                    else:
                                        px, py = 0, 0

                                    pts.extend([px, py])

                                    # 최소 외접원 계산
                                    ((cx, cy), radius) = cv2.minEnclosingCircle(u)
                                    pts.append(int(radius))
                                else:
                                    # 감지된 물체가 없는 경우
                                    u = np.array([[[0, 0]], [[1, 0]], [[2, 0]], [[2, 1]], [[2, 2]], [[1, 2]], [[0, 2]], [[0, 1]]])
                                    pts.extend([frame_count, 3, 0, 0, 0])

                                # 진행률 업데이트 (5프레임마다)
                                if frame_count % 5 == 0:
                                    progress = frame_count / length
                                    progress_container.progress(progress)

                            except Exception as e:
                                st.write(f"\n[ERROR] 프레임 {frame_count} 처리 중 오류 발생 : {str(e)}")
                                continue

                        # 진행률 표시 컨테이너 제거
                        progress_bar.empty()
                        progress_text.empty()

                        st.write(f"처리된 총 프레임 수 :  {frame_count}")
                        st.write(f"수집된 데이터 포인트 수 : {len(pts)}")
                        st.write("\n-> 분석 완료")

                        k = list(pts)
                        array_k = np.array(k)

                        frame_no = array_k[0::5]
                        timesteps = len(frame_no)
                        frame_no2 = np.reshape(frame_no, (timesteps, 1))

                        color = array_k[1::5]
                        color2 = np.reshape(color, (timesteps, 1))

                        x_value = array_k[2::5]
                        x_value2 = np.reshape(x_value, (timesteps, 1))

                        y_value = array_k[3::5]
                        y_value2 = np.reshape(y_value, (timesteps, 1))

                        radius2 = array_k[4::5]
                        radius3 = np.reshape(radius2, (timesteps, 1))

                        points = np.hstack([frame_no2, color2, x_value2, y_value2, radius3])

                        # 프레임 레이트를 이용한 시간 간격 계산 (초 단위)
                        time_interval = 1.0 / frame_rate
                        
                        # 초당 이동거리 계산을 위한 배열
                        distance_g = np.array([])

                        for i in range(timesteps - 1):
                            if (points[i][1] != 3 and points[i + 1][1] != 3) and (points[i][1] == 2 and points[i + 1][1] == 2):
                                a = points[i + 1][2] - points[i][2]
                                b = points[i + 1][3] - points[i][3]
                                rr = points[i][4]
                                
                                # 초당 이동거리로 계산 (프레임 간 이동거리를 시간 간격으로 나누고 반지름으로 정규화)
                                delta_g = (np.sqrt((a * a) + (b * b))) / rr / time_interval
                                
                                distance_g = np.append(distance_g, delta_g)
                            else:
                                distance_g = np.append(distance_g, 0)

                        # 초당 이동거리의 평균과 표준편차 계산
                        # 임계값도 프레임 레이트에 맞게 조정 (기존 6에서 프레임 레이트를 고려한 값으로)
                        # 30fps 기준으로 6이었다면, 초당 이동거리로는 6*30=180 정도가 됨
                        threshold = 180  # 조정된 임계값
                        
                        mean_g = np.mean([ggg for ggg in distance_g if ggg < threshold])
                        std_g = np.std([ggg for ggg in distance_g if ggg < threshold])
                        x_test = np.array([[mean_g, std_g]])

                        # 결과의 일관성을 위해 랜덤 시드 설정
                        np.random.seed(42)
                        
                        # 기존 훈련 데이터 로드
                        x_train = np.loadtxt('x_train.csv', delimiter=',')

                        # 고정된 정규화 범위 사용
                        scaler = MinMaxScaler(feature_range=(0, 1))
                        x_train_scaled = scaler.fit_transform(x_train)
                        x_test_scaled = scaler.transform(x_test)

                        # SVM 모델 생성
                        clf = svm.OneClassSVM(nu=0.1, kernel="rbf", gamma=0.1)
                        clf.fit(x_train_scaled)

                        st.write("---")
                        st.subheader("최종 판정")

                        y_pred_test = clf.predict(x_test_scaled)
                        str4 = str(round(clf.decision_function(x_test_scaled)[0], 4))
                        st.write(f"판단 점수: {str4}")
                        
                        # 분석 결과는 정상적으로 계산하되, 제한 위배 시 자동으로 Fail 처리
                        if y_pred_test == 1 and is_video_length_valid and is_photo_count_valid:
                            str3 = 'Pass'
                            st.write('EGD 수행이 적절하게 진행되어 EMT 과정에서 합격하셨습니다. 수고하셨습니다.')
                        else:
                            str3 = 'Fail'
                            if not is_video_length_valid or not is_photo_count_valid:
                                st.write('동영상 길이 또는 사진 수가 요구사항을 충족하지 않아 불합격입니다.')
                            else:
                                st.write('EGD 수행이 적절하게 진행되지 못해 불합격입니다. 다시 도전해 주세요.')
                        
                        # 모든 경우에 progress 폴더에 결과 기록
                        try:
                            bucket = storage.bucket('amcgi-bulletin.appspot.com')
                            current_date = datetime.now(timezone.utc).strftime("%Y%m%d")
                            video_duration_str = f"{int(video_duration // 60)}분{int(video_duration % 60)}초"
                            progress_filename = f"{position}*{name}*{current_date}*{video_duration_str}*{mean_g:.4f}*{std_g:.4f}*{str4}*{str3}"
                            progress_blob = bucket.blob(f"Simulator_training/EMT/EMT_result_progress/{progress_filename}")
                            
                            # 빈 파일 생성하여 업로드 (파일명에 모든 정보 포함)
                            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_progress_file:
                                # 파일에 내용 추가 (최소한의 내용이라도 필요)
                                temp_progress_file.write(f"EMT 훈련 결과: {position}, {name}, {current_date}")
                                temp_progress_file_path = temp_progress_file.name
                            
                            try:
                                progress_blob.upload_from_filename(temp_progress_file_path)
                                st.success("분석 결과가 기록되었습니다.")
                            except Exception as upload_error:
                                st.error(f"파일 업로드 중 오류 발생: {str(upload_error)}")
                            finally:
                                # 임시 파일 삭제
                                if os.path.exists(temp_progress_file_path):
                                    os.unlink(temp_progress_file_path)
                        except Exception as e:
                            st.error(f"분석 결과 기록 중 오류 발생: {str(e)}")
                        
                    except Exception as e:
                        st.write(f"\n[ERROR] 비디오 처리 중 치명적 오류 발생 : {str(e)}")
                    finally:
                        # 분석 완료 후 정리
                        camera.release()

            # 동영상 파일 업로드 처리 - BMP 파일 처리와 별도로 실행
            if video_file_path:
                try:
                    # 파일이 실제로 존재하는지 확인
                    if not os.path.exists(video_file_path):
                        st.error(f"파일을 찾을 수 없습니다: {video_file_path}")
                    else:
                        bucket = storage.bucket('amcgi-bulletin.appspot.com')
                        extension = os.path.splitext(video_file_path)[1]  # 파일 확장자 추출
                        current_date = datetime.now(timezone.utc).strftime("%Y%m%d")
                        video_file_name = f"{position}*{name}*EMT_result*{current_date}{extension}"
                        
                        # 동영상 업로드 - 조건에 따라 다른 폴더에 저장
                        if str3 == "Pass" and is_photo_count_valid and is_video_length_valid:
                            # Pass이고 사진 숫자와 동영상 길이가 모두 유효한 경우
                            video_blob = bucket.blob(f"Simulator_training/EMT/EMT_result_passed/{video_file_name}")
                            video_blob.upload_from_filename(
                                video_file_path,
                                content_type='video/x-msvideo'  # 추가: AVI 형식을 위한 MIME 타입
                            )
                            st.success("동영상이 성공적으로 전송되었습니다.")
                        else:
                            # Fail이거나 사진 숫자 또는 동영상 길이가 유효하지 않은 경우
                            video_blob = bucket.blob(f"Simulator_training/EMT/EMT_result_failed/{video_file_name}")
                            video_blob.upload_from_filename(
                                video_file_path,
                                content_type='video/x-msvideo'  # 추가: AVI 형식을 위한 MIME 타입
                            )
                            
                            # 실패 이유 메시지 표시
                            if str3 != "Pass":
                                st.warning("평가 결과가 'fail'이므로 동영상은 실패 폴더에 업로드했습니다.")
                            elif not is_photo_count_valid:
                                st.warning("사진의 숫자가 62-66 범위를 벗어나므로 동영상은 실패 폴더에 업로드했습니다.")
                            elif not is_video_length_valid:
                                st.warning("동영상 길이가 5분-5분 30초 범위를 벗어나므로 동영상은 실패 폴더에 업로드했습니다.")
                except Exception as e:
                    st.error(f"동영상 전송 중 오류 발생: {str(e)}")
                    st.error(f"파일 경로: {video_file_path}")

            # BMP 파일 처리 (조건이 모두 충족될 때만 이미지 생성 및 업로드)
            if has_bmp and video_duration > 0 and is_photo_count_valid and is_video_length_valid and str3 == "Pass":
                # A4 크기 설정 (300 DPI 기준)
                a4_width = 2480
                a4_height = 3508
                images_per_row = 8
                padding = 20

                # A4 크기의 빈 이미지 생성
                result_image = Image.new('RGB', (a4_width, a4_height), 'white')
                draw = ImageDraw.Draw(result_image)

                # 각 이미지의 크기 계산
                single_width = (a4_width - (padding * (images_per_row + 1))) // images_per_row

                # 이미지 배치
                x, y = padding, padding
                for idx, bmp_file in enumerate(bmp_files):
                    img = Image.open(bmp_file)
                    img.thumbnail((single_width, single_width))
                    result_image.paste(img, (x, y))
                    
                    x += single_width + padding
                    if (idx + 1) % images_per_row == 0:
                        x = padding
                        y += single_width + padding
                
                # 텍스트 추가
                font_size = 70
                text_color = (0, 0, 0)  # 검은색

                try:
                    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                    font = ImageFont.truetype(font_path, font_size)
                except OSError:
                    try:
                        font_path = "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"
                        font = ImageFont.truetype(font_path, font_size)
                    except OSError:
                        try:
                            font_path = "C:/Windows/Fonts/malgun.ttf"
                            font = ImageFont.truetype(font_path, font_size)
                        except OSError:
                            font = ImageFont.load_default()
                            st.write("시스템 폰트를 찾을 수 없어 기본 폰트를 사용합니다.")

                # 동영상 길이 저장
                video_length = f"{int(video_duration // 60)} min {int(video_duration % 60)} sec"

                # 추가할 텍스트
                text = f"Photo number: {len(bmp_files)}\nDuration: {video_length}\nResult: {str3}\nSVM_value: {str4}\nMean distance: {mean_g:.4f}\nStd distance: {std_g:.4f}"

                # 텍스트 크기 계산
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]

                # 텍스트 위치 계산 (왼쪽 정렬, 맨 아래 줄)
                x = padding
                y = a4_height - text_height - padding * 2

                # 텍스트 그리기
                draw.text((x, y), text, fill=text_color, font=font, align="left")
                st.divider()
                st.subheader("이미지 전송 과정")
                
                # 결과 이미지 크기 조정
                width, height = result_image.size
                result_image = result_image.resize((width // 2, height // 2), Image.Resampling.LANCZOS)
                
                # 결과 이미지 저장 - 하이픈(-)을 구분자로 사용
                temp_image_path = os.path.join(temp_dir, f'{position}-{name}-EMT_result.png')
                result_image.save(temp_image_path, format='PNG')
                
                try:
                    bucket = storage.bucket('amcgi-bulletin.appspot.com')

                    # Pass이고 모든 조건이 충족된 경우 -> EMT_result_passed 폴더
                    if str3 == "Pass" and is_photo_count_valid:
                        firebase_path = f"Simulator_training/EMT/EMT_result_passed/{position}-{name}-EMT_result.png"
                        result_blob = bucket.blob(firebase_path)
                        result_blob.upload_from_filename(
                            temp_image_path,
                            content_type='image/png'  # MIME-Type 명시
                        )

                        # 로그 파일 생성 및 전송 (Pass인 경우에만)
                        log_text = (
                            f"EMT_result image uploaded by {name} ({position}) "
                            f"on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n"
                        )
                        log_file_path = os.path.join(temp_dir, f"{position}-{name}-EMT_result.txt")
                        with open(log_file_path, 'w') as f:
                            f.write(log_text)

                        log_blob = bucket.blob(f"Simulator_training/EMT/log_EMT_result/{position}*{name}*EMT_result")
                        log_blob.upload_from_filename(log_file_path)

                        # 추가: EMT_result_progress 폴더에 진행 상황 기록
                        current_date = datetime.now(timezone.utc).strftime("%Y%m%d")
                        video_duration_str = f"{int(video_duration // 60)}분{int(video_duration % 60)}초"
                        progress_filename = f"{position}*{name}*{current_date}*{video_duration_str}*{mean_g:.4f}*{std_g:.4f}*{str4}*{str3}"
                        progress_blob = bucket.blob(f"Simulator_training/EMT/EMT_result_progress/{progress_filename}")
                        
                        # 빈 파일 생성하여 업로드 (파일명에 모든 정보 포함)
                        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_progress_file:
                            temp_progress_file.write(f"EMT 훈련 결과: {position}, {name}, {current_date}")
                            temp_progress_file_path = temp_progress_file.name
                        
                        progress_blob.upload_from_filename(temp_progress_file_path)
                        os.unlink(temp_progress_file_path)

                    else:
                        # Fail(또는 조건이 충족되지 않은 경우) -> EMT_result_failed 폴더
                        firebase_path = f"Simulator_training/EMT/EMT_result_failed/{position}-{name}-EMT_result.png"
                        result_blob = bucket.blob(firebase_path)
                        result_blob.upload_from_filename(
                            temp_image_path,
                            content_type='image/png'  # MIME-Type 명시
                        )
                        
                        # 추가: EMT_result_progress 폴더에 진행 상황 기록 (실패한 경우에도)
                        current_date = datetime.now(timezone.utc).strftime("%Y%m%d")
                        video_duration_str = f"{int(video_duration // 60)}분{int(video_duration % 60)}초"
                        progress_filename = f"{position}*{name}*{current_date}*{video_duration_str}*{mean_g:.4f}*{std_g:.4f}*{str4}*{str3}"
                        progress_blob = bucket.blob(f"Simulator_training/EMT/EMT_result_progress/{progress_filename}")
                        
                        # 빈 파일 생성하여 업로드 (파일명에 모든 정보 포함)
                        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_progress_file:
                            temp_progress_file.write(f"EMT 훈련 결과: {position}, {name}, {current_date}")
                            temp_progress_file_path = temp_progress_file.name
                        
                        progress_blob.upload_from_filename(temp_progress_file_path)
                        os.unlink(temp_progress_file_path)
                        
                        st.warning("이미지가 Fail 폴더로 전송되었습니다.")
                    
                    st.success(f"이미지가 성공적으로 전송되었습니다.")
                    
                    st.image(temp_image_path, use_container_width=True)
                except Exception as e:
                    st.error(f"이미지 전송 중 오류 발생: {str(e)}")
            
            # 임시 파일 정리
            try:
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        st.error(f"파일 삭제 중 오류 발생: {str(e)}")
                try:
                    os.rmdir(temp_dir)
                except:
                    pass
                
                st.success("평가가 완료되었습니다.")
            except Exception as e:
                st.error(f"임시 파일 정리 중 오류 발생: {str(e)}")

else:
    st.warning('Please log in to read more.')