import streamlit as st
import os
import tempfile
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, storage
from utils.auth import check_login, handle_logout

# Set page to wide mode
st.set_page_config(page_title="LHT Simulator Training", layout="wide")

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
if 'show_lht_video' not in st.session_state:
    st.session_state.show_lht_video = False
if 'show_lht_expert_video' not in st.session_state:
    st.session_state.show_lht_expert_video = False

# Title
st.title("LHT Simulator Training")

st.markdown("---")  # 구분선 추가

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
            st.session_state.show_lht_expert_video = not st.session_state.show_lht_expert_video
        
        # 비디오 플레이어 표시
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

                log_blob = bucket.blob(f"log/{log_file_name}")
                log_blob.upload_from_filename(temp_file_path)
                os.unlink(temp_file_path)

                st.success(f"{video_file_name} 파일이 성공적으로 업로드되었습니다!")

        except Exception as e:
            st.error(f"업로드 중 오류가 발생했습니다: {e}")

except Exception as e:
    st.error(f"LHT orientation 동영상 재생 중 오류가 발생했습니다: {e}")
