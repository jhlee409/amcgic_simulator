import streamlit as st
import os
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, storage
import tempfile
from utils.auth import check_login, handle_logout

# Set page to wide mode
st.set_page_config(page_title="MT - Memory Training", layout="wide")

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

# 세션 상태 초기화
if 'show_mt_video' not in st.session_state:
    st.session_state.show_mt_video = False

# Title and Instructions
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

st.subheader("MT demo 동영상 시청")
st.markdown("한 피교육자가 제출한 인공지능 분석 99점인 암기 구술 동영상입니다. 합격 기준은 80점 이상입니다.")
try:
    bucket = storage.bucket('amcgi-bulletin.appspot.com')
    demonstration_blob = bucket.blob('Simulator_training/MT/MT_demo.mp4')
    if demonstration_blob.exists():
        demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
        
        # 동영상 시청 버튼
        if st.button("동영상 시청"):
            st.session_state.show_mt_video = not st.session_state.show_mt_video
        
        # 비디오 플레이어 표시
        if st.session_state.show_mt_video:
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
            log_blob = bucket.blob(f"log/{log_file_name}")
            log_blob.upload_from_filename(temp_file_path)

            # Remove temporary log file
            os.unlink(temp_file_path)

            # Success message
            st.success(f"{video_file_name} 파일이 성공적으로 업로드되었습니다!")
    except Exception as e:
        # Error message
        st.error(f"업로드 중 오류가 발생했습니다: {e}")

# 로그아웃 버튼
st.sidebar.markdown("---")
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
                st.session_state.clear()
                st.success("로그아웃 되었습니다.")
                st.rerun()
                
            else:
                st.error("로그인 기록을 찾을 수 없습니다.")
                
        except Exception as e:
            st.error(f"로그아웃 처리 중 오류가 발생했습니다: {str(e)}")
