import streamlit as st
import os
import tempfile
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, storage
import base64

# Set page to wide mode
st.set_page_config(page_title="Hemoclip simulator training", layout="wide")

if "logged_in" in st.session_state and st.session_state['logged_in']:
    # 세션에서 사용자 정보 가져오기
    name = st.session_state['name']
    position = st.session_state['position']

    # 로그아웃 버튼
    if st.sidebar.button("Logout", key="logout_button"):
        st.session_state['logged_in'] = False
        st.success("로그아웃 되었습니다.")
        st.stop()

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

    st.header("Hemoclip simulator training")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.markdown("이 페이지는 Hemoclip simulator을 대상으로 한 Hemoclip 수행에 도움이 되는 자료를 제공하는 페이지입니다.")
        st.write("Hemoclip simulator 실습 전에 'hemoclip_orientation.mp4' 동영상을 예습하세요.")
    st.write("---")
   
    st.subheader("Hemoclip simulator orientation")

    # 동영상 다운로드 방지를 위한 CSS 스타일 추가
    st.markdown("""
        <style>
        /* 동영상 요소에 대한 컨텍스트 메뉴 비활성화 */
        .stVideo > div {
            position: relative;
        }
        .stVideo > div::after {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
        }
        .stVideo video {
            pointer-events: auto !important;
        }
        </style>
        <script>
        document.addEventListener('contextmenu', function(e) {
            if (e.target.tagName === 'VIDEO') {
                e.preventDefault();
            }
        }, false);
        </script>
    """, unsafe_allow_html=True)

    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        demonstration_blob = bucket.blob('Simulator_training/Hemoclip/hemoclip_orientation.mp4')
        if demonstration_blob.exists():
            # 동영상 시청 버튼
            if st.button("동영상 시청", key="expert_demo_view"):
                # 동영상 데이터를 임시 파일로 저장
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                    temp_file.write(demonstration_blob.download_as_bytes())
                    temp_file_path = temp_file.name
                
                # 동영상 플레이어 표시
                st.video(temp_file_path)
                
                # 임시 파일 삭제
                os.unlink(temp_file_path)
                
                # 로그 파일 생성 및 업로드
                current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                    log_content = f"APC_orientation video viewed by {name} ({position}) on {current_date}"
                    temp_file.write(log_content)
                    temp_file_path = temp_file.name

                # Firebase Storage에 로그 파일 업로드
                log_blob = bucket.blob(f"Simulator_training/Hemoclip/log_Hemoclip/{position}*{name}*Hemoclip")
                log_blob.upload_from_filename(temp_file_path)
                os.unlink(temp_file_path)
        else:
            st.error("Hemoclip simulator orientation 시범 동영상 파일을 찾을 수 없습니다.")

    except Exception as e:
        st.error(f"Hemoclip simulator orientation 동영상 파일 재생 중 오류가 발생했습니다: {e}")

   
else:
    st.warning('Please log in to read more.')