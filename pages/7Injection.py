import streamlit as st
import os
import tempfile
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, storage
from utils.auth import check_login, handle_logout

# Set page to wide mode
st.set_page_config(page_title="Injection simulator training", layout="wide")

# 로그인 상태 확인
name, position = check_login()

# Initialize Firebase (기존 코드 유지)
# ... existing code ...

# 페이지 선택을 위한 드롭다운 메뉴
selected_page = st.sidebar.selectbox(
    "시뮬레이터 선택",
    ["Default", "PEG", "APC", "Injection", "Hemoclip"],
    key="page_selection",
    index=3  # Injection 페이지의 경우 기본값을 Injection으로 설정
)

# 선택된 페이지로 리다이렉트
if selected_page != "Injection":
    if selected_page == "Default":
        st.switch_page("Home.py")
    else:
        st.switch_page(f"pages/{selected_page}.py")

st.header("Injection simulator training")
with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
    st.markdown("이 페이지는 Injection simulator을 대상으로 한 Injection 수행에 도움이 되는 자료를 제공하는 페이지입니다.")
    st.write("Injection simulator 실습 전에 예습 영상을 시청하세요.")
st.write("---")

# 세션 상태 초기화
if 'show_video' not in st.session_state:
    st.session_state.show_video = False

# 동영상 시청 버튼을 로그아웃 버튼 위에 배치
if st.sidebar.button("본영상 시청", key="watch_video"):
    # 비디오 표시 상태 토글
    st.session_state.show_video = not st.session_state.show_video
    
    if st.session_state.show_video:
        # 로그 파일 생성 및 업로드
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            log_content = f"Injection_orientation video watched by {name} ({position}) on {current_date}"
            temp_file.write(log_content)
            temp_file_path = temp_file.name

        # Firebase Storage에 로그 파일 업로드
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        log_blob = bucket.blob(f"Simulator_training/Injection/log_Injection/{position}*{name}*Injection")
        log_blob.upload_from_filename(temp_file_path)
        os.unlink(temp_file_path)

# 로그아웃 처리 (한 번만 호출)
handle_logout()

# 1:9 비율의 두 컬럼 생성
col1, col2 = st.columns([1, 9])

try:
    bucket = storage.bucket('amcgi-bulletin.appspot.com')
    
    with col1:
        if selected_page == "Default":
            # default 미리보기 비디오 표시
            default_prevideo_blob = bucket.blob('Simulator_training/default/default_prevideo.mp4')
            if default_prevideo_blob.exists():
                default_prevideo_url = default_prevideo_blob.generate_signed_url(expiration=timedelta(minutes=15))
                st.video(default_prevideo_url)
        else:  # Injection 선택시
            # Injection 미리보기 비디오 표시
            prevideo_blob = bucket.blob('Simulator_training/Injection/Injection_orientation_prevideo.mp4')
            if prevideo_blob.exists():
                prevideo_url = prevideo_blob.generate_signed_url(expiration=timedelta(minutes=15))
                st.video(prevideo_url)
            
            # 문서 파일 표시
            doc_blob = bucket.blob('Simulator_training/Injection/Injection_orientation.docx')
            if doc_blob.exists():
                doc_url = doc_blob.generate_signed_url(expiration=timedelta(minutes=15))
                st.markdown(f"[Injection orientation 문서 다운로드]({doc_url})")

    # 본영상 시청 버튼이 눌렸을 때만 오른쪽 컬럼에 동영상 표시
    with col2:
        if 'show_video' in st.session_state and st.session_state.show_video:
            main_video_blob = bucket.blob('Simulator_training/Injection/Injection_orientation.mp4')
            if main_video_blob.exists():
                video_url = main_video_blob.generate_signed_url(expiration=timedelta(minutes=15))
                video_html = f'''
                <div style="display: flex; justify-content: center;">
                    <video width="1300" controls controlsList="nodownload">
                        <source src="{video_url}" type="video/mp4">
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
    st.error(f"파일 로딩 중 오류가 발생했습니다: {e}")