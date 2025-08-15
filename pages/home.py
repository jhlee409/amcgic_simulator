import streamlit as st
import os
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, storage
import tempfile
from utils.auth import check_login, handle_logout

# Set page to wide mode
st.set_page_config(page_title="Simulator Training Home", layout="wide")

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
name, position = check_login()

if name and position:  # 로그인 성공 시
    # 페이지 선택을 위한 드롭다운 메뉴
    selected_page = st.sidebar.selectbox(
        "시뮬레이터 선택",
        ["Default", "PEG", "APC", "Injection", "Hemoclip"],
        key="page_selection",
        index=0  # Default 페이지의 경우 기본값을 Default로 설정
    )

    # 선택된 페이지로 리다이렉트
    if selected_page != "Default":
        st.switch_page(f"pages/{selected_page}.py")

    # Default 페이지 (홈 페이지) 내용
    st.title("Simulator Training Home")
    st.markdown("로그인되었습니다. 사이드바에서 원하는 시뮬레이터를 선택하세요.")
    
    # 사용자 정보 표시
    st.subheader("👤 사용자 정보")
    st.info(f"**이름:** {name}  |  **직책:** {position}")
    
    # 시뮬레이터 선택 안내
    st.subheader("🎯 시뮬레이터 선택")
    st.markdown("사이드바에서 원하는 시뮬레이터를 선택하여 훈련을 시작하세요:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔴 PEG")
        st.markdown("PEG 시뮬레이터 훈련")
        
        st.markdown("### 🔵 APC")
        st.markdown("APC 시뮬레이터 훈련")
    
    with col2:
        st.markdown("### 💉 Injection")
        st.markdown("Injection 시뮬레이터 훈련")
        
        st.markdown("### 📎 Hemoclip")
        st.markdown("Hemoclip 시뮬레이터 훈련")
    
    # 로그아웃 버튼
    st.sidebar.markdown("---")
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

else:
    st.warning('로그인이 필요합니다.')
    st.stop()
