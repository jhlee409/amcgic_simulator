import streamlit as st
import os
import tempfile
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, storage
from utils.auth import check_login, handle_logout

# Set page to wide mode
st.set_page_config(page_title="NexPowder Training", layout="wide")

# 로그인 상태 확인
if "logged_in" not in st.session_state or not st.session_state['logged_in']:
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
if 'show_nexpowder_video' not in st.session_state:
    st.session_state.show_nexpowder_video = False

# 사이드바에 사용자 정보와 로그아웃 버튼 배치
st.sidebar.markdown("---")  # 구분선 추가
st.sidebar.info(f"**사용자**: {name} ({position})")

# 로그아웃 버튼
if st.sidebar.button("로그아웃", key="nexpowder_logout"):
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
            if '*' in login_time_str:
                login_time_str = login_time_str.split('*')[-1]
            
            # UTC 시간으로 파싱하여 시간대 정보 추가
            login_time = datetime.strptime(login_time_str, "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
            
            # 시간 차이 계산 (초 단위)
            time_duration = int((logout_time - login_time).total_seconds())
            
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

# Title
st.title("NexPowder Training")

st.markdown("---")  # 구분선 추가

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

                log_blob = bucket.blob(f"log/{position}*{name}*NexPowder")
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
