import streamlit as st
import os
import cv2
import numpy as np
from collections import deque
import pandas as pd
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, storage
import tempfile
from utils.auth import check_login, handle_logout
from PIL import Image, ImageDraw, ImageFont
import requests
import tempfile

# Set page to wide mode
st.set_page_config(page_title="Simualtor dvanced Training", layout="wide")

# 로그인 상태 확인
if "logged_in" not in st.session_state or not st.session_state['logged_in']:
    try:
        # Firebase Storage에서 기존 로그 폴더 삭제
        bucket = storage.bucket()
        
        # login과 logout 폴더의 모든 파일 삭제
        login_blobs = list(bucket.list_blobs(prefix='log_login/'))
        logout_blobs = list(bucket.list_blobs(prefix='log_logout/'))
        
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
    except Exception as e:
        st.error(f"로그 폴더 삭제 중 오류가 발생했습니다: {str(e)}")
        
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
for video_type in ['lht', 'evl', 'hemoclip', 'injection', 'nexpowder', 'apc', 'peg']:
    if f'show_{video_type}_video' not in st.session_state:
        st.session_state[f'show_{video_type}_video'] = False

# 사이드바에 드롭다운 메뉴와 로그아웃 버튼 배치
selected_option = st.sidebar.selectbox(
    "세부항목 선택",
    ["LHT", "Hemoclip", "Injection", "EVL", "APC", "NexPowder", "PEG"]
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
                
                # 파일 이름에서 시간 부분만 추출
                # 파일 이름 형식이 'Staff이진혁login*2025_03_13_21_22_49'와 같은 경우
                # '*' 기호로 분리하여 마지막 부분(시간)만 가져옴
                if '*' in login_time_str:
                    login_time_str = login_time_str.split('*')[-1]
                
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
    for video_type in ['lht', 'evl', 'hemoclip', 'injection', 'nexpowder', 'apc', 'peg']:
        st.session_state[f'show_{video_type}_video'] = False
    st.session_state.previous_selection = selected_option

# Title
st.title("Simulaor training advanced course orientation")

st.markdown("---")  # 구분선 추가

# 선택된 옵션에 따라 다른 기능 실행
if selected_option == "LHT":
    st.header("LHT_skill_evaluation")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.markdown("이 페이지는 LHT simulator을 대상으로 한 LHT 검사 수행에 도움이 되는 자료를 제공하고, 수행의 적절성을 평가하는 페이지입니다.")
        st.markdown("먼저 LHT orientation 동영상을 예습하세요.")
        st.markdown("시범 동영상을 잘 보고 미러링을 열심히 하시기 바랍니다.")
        st.markdown("수행에 자신이 생기면 동영상을 녹화하여 업로드하세요.")
    st.write("---")

    st.subheader("LHT orientation 동영상")
    try:
        demonstration_blob = bucket.blob('Simulator_training/LHT/LHT_orientation.mp4')
        if demonstration_blob.exists():
            demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
            
            if st.button("동영상 시청", key="lht_video"):
                st.session_state.show_lht_video = not st.session_state.show_lht_video
                
                # 로그 정보 전송을 제거하여 버튼 클릭 시 로그가 기록되지 않도록 수정
            if st.session_state.show_lht_video:
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

        st.write("---")
        
        st.subheader("전문가 시범 동영상")
        st.write("전문가가 수행한 LHT 시범 동영상입니다. 잘보고 어떤 점에서 초심자와 차이가 나는지 연구해 보세요.")
        demonstration_blob = bucket.blob('Simulator_training/LHT/LHT_expert_demo.mp4')
        if demonstration_blob.exists():
            demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
            
            # 동영상 시청 버튼
            if st.button("동영상 시청", key="lht_expert_video"):
                if "show_lht_expert_video" not in st.session_state:
                    st.session_state.show_lht_expert_video = True
                else:
                    st.session_state.show_lht_expert_video = not st.session_state.show_lht_expert_video
            
            # 비디오 플레이어 표시
            if "show_lht_expert_video" not in st.session_state:
                st.session_state.show_lht_expert_video = False
                
            if st.session_state.show_lht_expert_video:
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
            st.error("LHT 전문가 시범 동영상 파일을 찾을 수 없습니다.")

        st.write("---")

        st.subheader("수행 동영상 파일 업로드")
        uploaded_file = st.file_uploader("업로드할 암기 동영상(mp4, avi)을 선택하세요 (100 MB 이하로 해주세요.):", type=["mp4", "avi"])

        if uploaded_file:
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_video_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(temp_video_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    current_date = datetime.now().strftime("%Y-%m-%d")
                    extension = os.path.splitext(uploaded_file.name)[1]
                    video_file_name = f"{position}*{name}*LHT_result{extension}"

                    video_blob = bucket.blob(f"Simulator_training/LHT/LHT_result/{video_file_name}")
                    video_blob.upload_from_filename(temp_video_path, content_type=uploaded_file.type)

                    log_file_name = f"{position}*{name}*LHT"
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                        log_content = f"LHT_result video uploaded by {name} ({position}) on {current_date}"
                        temp_file.write(log_content)
                        temp_file_path = temp_file.name

                    log_blob = bucket.blob(f"Simulator_training/LHT/log_LHT/{log_file_name}")
                    log_blob.upload_from_filename(temp_file_path)
                    os.unlink(temp_file_path)

                    st.success(f"{video_file_name} 파일이 성공적으로 업로드되었습니다!")

            except Exception as e:
                st.error(f"업로드 중 오류가 발생했습니다: {e}")

    except Exception as e:
        st.error(f"LHT orientation 동영상 재생 중 오류가 발생했습니다: {e}")

elif selected_option == "EVL":
    st.header("EVL simulator training")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.markdown("이 페이지는 EVL simulator을 대상으로 한 EVL 검사 수행에 도움이 되는 자료를 제공하는 페이지입니다.")
        st.write("우리 병원에서는 Cook medical에서 생산되는 6 shooter multiband를  사용하고 있습니다.")
        st.write("이 multiband 사용 방법과 마지막에 expert의 시범 동영상을 예습하세요.")
    st.write("---")

    st.subheader("EVL multiband 사용방법 및 demo")
    try:
        demonstration_blob = bucket.blob('Simulator_training/EVL/EVL multiband 사용방법 및 demo.mp4')
        if demonstration_blob.exists():
            demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
            
            if st.button("동영상 시청", key="evl_video"):
                st.session_state.show_evl_video = not st.session_state.show_evl_video
                
                if st.session_state.show_evl_video:
                    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                        log_content = f"EVL_orientation video watched by {name} ({position}) on {current_date}"
                        temp_file.write(log_content)
                        temp_file_path = temp_file.name

                    log_blob = bucket.blob(f"Simulator_training/EVL/log_EVL/{position}*{name}*EVL")
                    log_blob.upload_from_filename(temp_file_path)
                    os.unlink(temp_file_path)
            
            if st.session_state.show_evl_video:
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
        st.error(f"EVL 시범 동영상 파일 재생 중 오류가 발생했습니다: {e}")

elif selected_option == "Hemoclip":
    st.header("Hemoclip simulator training")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.markdown("이 페이지는 Hemoclip simulator을 대상으로 한 Hemoclip 수행에 도움이 되는 자료를 제공하는 페이지입니다.")
        st.write("Hemoclip simulator 실습 전에 'hemoclip_orientation.mp4' 동영상을 예습하세요.")
    st.write("---")
   
    st.subheader("Hemoclip simulator orientation")
    try:
        demonstration_blob = bucket.blob('Simulator_training/Hemoclip/hemoclip_orientation.mp4')
        if demonstration_blob.exists():
            demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
            
            if st.button("동영상 시청", key="hemoclip_video"):
                st.session_state.show_hemoclip_video = not st.session_state.show_hemoclip_video
                
                if st.session_state.show_hemoclip_video:
                    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                        log_content = f"Hemoclip_orientation video watched by {name} ({position}) on {current_date}"
                        temp_file.write(log_content)
                        temp_file_path = temp_file.name

                    log_blob = bucket.blob(f"Simulator_training/Hemoclip/log_Hemoclip/{position}*{name}*Hemoclip")
                    log_blob.upload_from_filename(temp_file_path)
                    os.unlink(temp_file_path)
            
            if st.session_state.show_hemoclip_video:
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
        st.error(f"Hemoclip orientation 동영상 파일 재생 중 오류가 발생했습니다: {e}")

elif selected_option == "Injection":
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

                    log_blob = bucket.blob(f"Simulator_training/Injection/log_Injection/{position}*{name}*Injection")
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

elif selected_option == "NexPowder":
    st.header("NexPowder training")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.markdown("이 페이지는 NexPowder 검사 수행에 도움이 되는 자료를 제공하는 페이지입니다.")
        st.markdown("NexPowder 사용법 동영상과 cases를 예습하세요.")
        st.markdown("NexPowder를 장착하고 shooting 하는 방법을 보여주고 실제 사용하는 case를 보여주는 동영상입니다.")
    st.write("---")
   
    st.subheader("NexPowder 사용방법과 cases")
    try:
        demonstration_blob = bucket.blob('Simulator_training/NexPowder/Nexpowder 사용법과 cases.mp4')
        if demonstration_blob.exists():
            demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
            
            if st.button("동영상 시청", key="nexpowder_video"):
                st.session_state.show_nexpowder_video = not st.session_state.show_nexpowder_video
                
                if st.session_state.show_nexpowder_video:
                    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                        log_content = f"NexPowder_orientation video watched by {name} ({position}) on {current_date}"
                        temp_file.write(log_content)
                        temp_file_path = temp_file.name

                    log_blob = bucket.blob(f"Simulator_training/NexPowder/log_NexPowder/{position}*{name}*NexPowder")
                    log_blob.upload_from_filename(temp_file_path)
                    os.unlink(temp_file_path)
            
            if st.session_state.show_nexpowder_video:
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
        st.error(f"NexPowder 사용법 동영상 파일 재생 중 오류가 발생했습니다: {e}")

elif selected_option == "APC":
    st.header("APC simulator training")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.markdown("이 페이지는 APC simulator을 대상으로 한 APC 수행에 도움이 되는 자료를 제공하는 페이지입니다.")
        st.write("APC simulator 실습 전에 'APC_orientation.mp4' 동영상을 예습하세요.")
    st.write("---")

    st.subheader("APC simulator orientation")
    try:
        demonstration_blob = bucket.blob('Simulator_training/APC/APC_orientation.mp4')
        if demonstration_blob.exists():
            demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
            
            if st.button("동영상 시청", key="apc_video"):
                st.session_state.show_apc_video = not st.session_state.show_apc_video
                
                if st.session_state.show_apc_video:
                    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                        log_content = f"APC_orientation video watched by {name} ({position}) on {current_date}"
                        temp_file.write(log_content)
                        temp_file_path = temp_file.name

                    log_blob = bucket.blob(f"Simulator_training/APC/log_APC/{position}*{name}*APC")
                    log_blob.upload_from_filename(temp_file_path)
                    os.unlink(temp_file_path)
            
            if st.session_state.show_apc_video:
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
        st.error(f"APC orientation 동영상 파일 재생 중 오류가 발생했습니다: {e}")

elif selected_option == "PEG":
    st.header("PEG simulator training")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.markdown("이 페이지는 PEG simulator을 대상으로 한 PEG 수행에 도움이 되는 자료를 제공하는 페이지입니다.")
        st.write("PEG simulator 실습 전에 'PEG_orientation.mp4' 동영상을 예습하세요.")
    st.write("---")

    st.subheader('PEG simulator orientation')
    try:
        demonstration_blob = bucket.blob('Simulator_training/PEG/PEG_orientation.mp4')
        if demonstration_blob.exists():
            demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
            
            if st.button("동영상 시청", key="peg_video"):
                st.session_state.show_peg_video = not st.session_state.show_peg_video
                
                if st.session_state.show_peg_video:
                    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                        log_content = f"PEG_orientation video watched by {name} ({position}) on {current_date}"
                        temp_file.write(log_content)
                        temp_file_path = temp_file.name

                    log_blob = bucket.blob(f"Simulator_training/PEG/log_PEG/{position}*{name}*PEG")
                    log_blob.upload_from_filename(temp_file_path)
                    os.unlink(temp_file_path)
            
            if st.session_state.show_peg_video:
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
        st.error(f"PEG orientation 동영상 파일 재생 중 오류가 발생했습니다: {e}")

else:
    st.warning('Please log in to read more.')