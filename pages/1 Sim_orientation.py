import streamlit as st
import os
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, storage
import tempfile
from utils.auth import check_login, handle_logout

# Set page to wide mode
st.set_page_config(page_title="Sim Orientation", layout="wide")

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
if 'show_sim_video' not in st.session_state:
    st.session_state.show_sim_video = False

# Title and Instructions
st.title("Simulation Center EGD Basic Course Orientation")
with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
    st.markdown("이 페이지는 Simulation Center EGD basic course orientation 동영상을 시청하기 위한 페이지입니다.")
    st.markdown("끝낼 때는 반드시 로그아웃 버튼을 눌러 종결하세요. 그냥 종결하면 출석체크가 안됩니다.")

# Sim orientation 동영상 시청
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

                log_blob = bucket.blob(f"log/{position}*{name}*Sim")
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
