import streamlit as st
import os
from datetime import datetime, timedelta
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
from moviepy.editor import VideoFileClip
import google.generativeai as genai

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
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'amcgi-bulletin.appspot.com',
        'databaseURL': st.secrets["FIREBASE_DATABASE_URL"]  # Streamlit secrets에서 FIREBASE_DATABASE_URL사용
    })

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

# 로그아웃 처리
handle_logout()


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
                    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    st.subheader("MT (Memory Training)")
    
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
    
    # File uploader
    uploaded_file = None
    st.subheader("암기 영상 업로드")
    st.write("영상을 처리하는데 20-30초가 소요되니, 성공 메시지가 나올 때까지 기다려 주세요")
    uploaded_file = st.file_uploader("업로드할 암기 동영상(mp4)을 선택하세요 (100 MB 이하로 해주세요.):", type=["mp4"])

    if uploaded_file:
        try:
            # Gemini 초기화 및 설정
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            generation_config = {
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                generation_config=generation_config,
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                # 파일 저장 및 오디오 추출 부분
                temp_video_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_video_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # 진행 상태 표시
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 비디오에서 오디오 추출 (25% 진행)
                status_text.text("오디오 추출 중...")
                try:
                    video = VideoFileClip(temp_video_path)
                    temp_audio_path = os.path.join(temp_dir, f"{os.path.splitext(uploaded_file.name)[0]}.mp3")
                    video.audio.write_audiofile(
                        temp_audio_path,
                        codec='mp3',
                        bitrate='128k',
                        verbose=False,
                        logger=None
                    )
                    video.close()
                    progress_bar.progress(25)
                except Exception as e:
                    st.error(f"오디오 추출 중 오류가 발생했습니다: {e}")
                    video.close() if 'video' in locals() else None
                    st.stop()

                # Firebase에 파일 업로드 (50% 진행)
                status_text.text("파일 업로드 중...")
                current_date = datetime.now().strftime("%Y-%m-%d")
                video_extension = os.path.splitext(uploaded_file.name)[1]
                video_file_name = f"{position}*{name}*MT_result{video_extension}"
                audio_file_name = f"{position}*{name}*MT_result.mp3"

                bucket = storage.bucket('amcgi-bulletin.appspot.com')
                
                # 비디오 및 오디오 업로드
                video_blob = bucket.blob(f"Simulator_training/MT/MT_result/{video_file_name}")
                video_blob.upload_from_filename(temp_video_path, content_type=uploaded_file.type)
                
                audio_blob = bucket.blob(f"Simulator_training/MT/MT_result/{audio_file_name}")
                audio_blob.upload_from_filename(temp_audio_path, content_type='audio/mpeg')
                progress_bar.progress(50)

                # 음성 분석 준비 (75% 진행)
                status_text.text("음성 분석 준비 중...")
                # Firebase에서 업로드된 오디오 파일의 URL 가져오기
                audio_url = audio_blob.generate_signed_url(expiration=timedelta(minutes=10))
                gemini_file = genai.upload_file(temp_audio_path, mime_type="audio/mpeg")
                progress_bar.progress(75)

                # 음성 분석 (100% 진행)
                status_text.text("음성 분석 중...")
                try:
                    # 채팅 시작 및 응답 대기
                    chat = model.start_chat(history=[
                        {"role": "user", "parts": [gemini_file, st.secrets["GEMINI_PROMPT"]]}
                    ])
                    
                    # 응답 타임아웃 설정
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(chat.send_message, "평가를 시작해주세요")
                        try:
                            response = future.result(timeout=300)  # 5분 타임아웃
                        except concurrent.futures.TimeoutError:
                            raise Exception("음성 분석 시간이 초과되었습니다. 다시 시도해 주세요.")
                    
                    if not response or not response.text:
                        raise Exception("음성 분석 결과가 비어있습니다.")
                    
                    # 추출된 문장 수(x) 계산
                    extracted_sentences = len(response.text.split('\n'))
                    reference_sentences = 81
                    
                    # 점수 추출 및 계산
                    import re
                    score_match = re.search(r'정답률:\s*(\d+)%', response.text)
                    if not score_match:
                        raise Exception("점수 계산에 실패했습니다.")
                        
                    score = int(score_match.group(1))
                    progress_bar.progress(100)
                    status_text.empty()

                    # 결과 표시
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("추출된 문장 수", extracted_sentences)
                    with col2:
                        st.metric("기준 문장 수", reference_sentences)
                    with col3:
                        st.metric("최종 점수", f"{score}%")

                    if score >= 70:
                        st.success("합격입니다. 축하합니다!")
                    else:
                        st.error("안타깝게도 빠진 내용이 많습니다. 다시 시도해 주세요")

                except Exception as e:
                    st.error(f"음성 분석 중 오류가 발생했습니다: {str(e)}")
                    progress_bar.empty()
                    status_text.empty()
                    st.stop()

                # 로그 파일 생성 및 업로드
                log_file_name = f"{position}*{name}*MT"
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                    log_content = f"MT_result video uploaded by {name} ({position}) on {current_date}"
                    temp_file.write(log_content)
                    temp_file_path = temp_file.name

                log_blob = bucket.blob(f"Simulator_training/MT/log_MT/{log_file_name}")
                log_blob.upload_from_filename(temp_file_path)
                os.unlink(temp_file_path)

                st.success(f"{video_file_name} 파일이 성공적으로 업로드되었습니다!")

        except Exception as e:
            st.error(f"업로드 중 오류가 발생했습니다: {e}")

elif selected_option == "SHT":
    st.subheader("SHT (Scope Handling Training)")
    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        demonstration_blob = bucket.blob('Simulator_training/SHT/SHT_orientation.mp4')
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
    st.subheader("EMT (EGD Method Training)")
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
        demonstration_blob = bucket.blob('Simulator_training/EMT/EMT_expert_demo.avi')
        if demonstration_blob.exists():
            demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
            if st.download_button(
                label="동영상 다운로드",
                data=demonstration_blob.download_as_bytes(),
                file_name="EMT_expert_demo.avi",
                mime="video/avi"
            ):
                st.write("")
        else:
            st.error("EMT 시범 동영상 파일을 찾을 수 없습니다.")

    except Exception as e:
        st.error(f"EMT 시범 동영상 파일 다운로드 중 오류가 발생했습니다: {e}")

    st.write("---")

    st.subheader("수행 동영상 파일 업로드, 분석 및 최종 평가서 전송")

    uploaded_files = st.file_uploader(
        "분석할 동영상 파일들(mp4, avi)을 모두 선택해주세요.", 
        accept_multiple_files=True,
        type=['mp4', 'avi']
    )

    if uploaded_files:
        st.write(f"총 {len(uploaded_files)}개의 파일이 선택되었습니다.")
        
        for uploaded_file in uploaded_files:
            try:
                # 원본 파일의 전체 경로와 디렉토리 경로 가져오기
                original_path = uploaded_file.name
                original_dir = os.path.dirname(original_path)
                file_name = os.path.splitext(os.path.basename(original_path))[0]

                # 임시 파일로 동영상 저장
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(original_path)[1]) as temp_video:
                    temp_video.write(uploaded_file.getbuffer())
                    temp_video_path = temp_video.name

                # 동영상을 WAV로 변환하여 원본 위치에 저장
                video_clip = VideoFileClip(temp_video_path)
                wav_path = os.path.join(original_dir, f"{file_name}.wav")
                video_clip.audio.write_audiofile(wav_path)
                video_clip.close()

                # 임시 파일 삭제
                os.unlink(temp_video_path)

                st.success(f"{file_name}.wav 파일이 성공적으로 저장되었습니다!")

            except Exception as e:
                st.error(f"파일 처리 중 오류가 발생했습니다: {e}")

        st.divider() 
        st.success("평가가 완료되었습니다.")

else:
    st.warning('Please log in to read more.')