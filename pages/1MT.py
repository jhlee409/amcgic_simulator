import streamlit as st
import os
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, storage
import tempfile

# Set page to wide mode
st.set_page_config(page_title="MT", layout="wide")

if "logged_in" in st.session_state and st.session_state['logged_in']:
    # 세션에서 사용자 정보 가져오기
    name = st.session_state['name']
    position = st.session_state['position']

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
        firebase_admin.initialize_app(cred)

    # Title and Instructions
    st.title("Memory test")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.write("이 페이지는 Memory test 필요 자료를 다운 받고, 암기 동영상을 업로드하는 웹페이지입니다.")
        st.write("설명 문서 다운로드 버튼을 눌러, 검사과정을 설명한 docx 문서를 다운받으세요.")
        st.write("나레이션 mp3 다운로드 버튼을 눌러 설명을 읽어준 나레이션 파일을 다운 받으세요.")
        st.write("그냥 외우려고 하면 막연해서 잘 안 외어 집니다. EGD 수행 해설 동영상 2개를 시청하면 암기하는데 도움이됩니다.")
        st.write("충분하다고 판단되면 웹카메라로 암기하는 동영상을 만든 후 여기에 올려 주세요 단 동영상 형식은 mp4, 크기는 100 MB 이하로 해주세요.")
        st.write("암기할 때는 웹카메라를 응시하면서 말해야 합니다. 자꾸 다른 쪽으로 시선을 돌리면 부정행위로 분류될 수 있습니다.")
    st.write("---")

        # Initialize session state
    if 'name_selected' not in st.session_state:
        st.session_state.name_selected = False
    if 'show_file_list' not in st.session_state:
        st.session_state.show_file_list = False
    if 'download_clicked' not in st.session_state:
        st.session_state.download_clicked = False

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

    # Add mp4 download button

    st.subheader("전문가 EGD 수행 해설 동영상")
    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        demonstration1_blob = bucket.blob('EGD_variation/B1.mp4')
        if demonstration1_blob.exists():
            demonstration_url = demonstration1_blob.generate_signed_url(expiration=timedelta(minutes=15))
            if st.button("동영상 시청"):
                st.video(demonstration_url)
        else:
            st.error("EGD 해설 동영상 파일을 찾을 수 없습니다.")

    except Exception as e:
        st.error(f"EGD 해설 동영상 파일 다운로드 중 오류가 발생했습니다: {e}")

    st.write("---")

    # File uploader - only show if inputs are valid
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
                current_date = datetime.now().strftime("%Y-%m-%d")

                # Generate file names
                extension = os.path.splitext(uploaded_file.name)[1]  # Extract file extension
                video_file_name = f"{position}*{name}*MT_result{extension}"

                # Firebase Storage upload for video
                bucket = storage.bucket('amcgi-bulletin.appspot.com')
                video_blob = bucket.blob(f"Simulator_training/MT/MT_result/{video_file_name}")
                video_blob.upload_from_filename(temp_video_path, content_type=uploaded_file.type)

                # Generate log file name
                log_file_name = f"{position}*{name}*MT_result"

                # Create log file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                    log_content = f"MT_result video uploaded by {name} ({position}) on {current_date}"
                    temp_file.write(log_content)
                    temp_file_path = temp_file.name

                # Firebase Storage upload for log file
                log_blob = bucket.blob(f"Simulator_training/MT/log_MT_result/{log_file_name}")
                log_blob.upload_from_filename(temp_file_path)

                # Remove temporary log file
                os.unlink(temp_file_path)

                # Success message
                st.success(f"{video_file_name} 파일이 성공적으로 업로드되었습니다!")
                st.session_state.show_file_list = True
        except Exception as e:
            # Error message
            st.error(f"업로드 중 오류가 발생했습니다: {e}")

    # 로그아웃 버튼
    if "logged_in" in st.session_state and st.session_state['logged_in']:
        if st.sidebar.button("Logout"):
            st.session_state['logged_in'] = False
            st.success("로그아웃 되었습니다.")
    
else:
    st.warning('Please log in to read more.')
