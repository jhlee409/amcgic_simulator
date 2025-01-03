import streamlit as st
import os
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, storage
import tempfile

# Set page to wide mode
st.set_page_config(page_title="MT_results")

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
    st.write("설명 문서 다운로드 버튼을 눌러 암기할 검사과정을 설명한 docx 문서를 다운받으세요.")
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

st.subheader("로그인")
position = st.selectbox("직위를 선택해 주세요.", ["", "Staff", "F1", "F2", "R3", "Student"])
user_name = st.text_input("한글 이름을 입력하고 엔터를 쳐 주세요. (예: 이진혁):", key="user_name")
st.write("---")

def is_korean(text):
    # 한글 유니코드 범위: AC00-D7A3 (가-힣)
    return all('\uAC00' <= char <= '\uD7A3' for char in text if char.strip())

def on_download_click():
    st.session_state.download_clicked = True

# 입력값 검증
is_valid = True
if position == "" or not position:
    st.error("position을 선택해 주세요")
    is_valid = False
if not user_name:
    st.error("한글 이름을 입력하고 엔터를 쳐 주세요")
    is_valid = False
elif not is_korean(user_name):
    st.error("한글 이름을 입력하고 엔터를 쳐 주세요.")
    is_valid = False

# Add download button for EGD procedure document
if is_valid:
    doc_path = "EGD 시행 동작 순서 Bx 포함 2024.docx"
    st.subheader("설명 문서 다운로드")
    if os.path.exists(doc_path):
        with open(doc_path, "rb") as file:
            if st.download_button(
                label="설명 문서 다운로드",
                data=file,
                file_name="EGD 시행 동작 순서 Bx 포함 2024.docx",
                mime="application/msword",
                on_click=on_download_click
            ):
                st.write("")
                # Log download to Firebase
                bucket = storage.bucket('amcgi-bulletin.appspot.com')
                log_blob = bucket.blob(f"MT_results/log_MT_download/{position}*{user_name}*'MT_doc_downloaded'")
                log_blob.upload_from_string(position + "_" + user_name + "_MT_doc_downloaded" + "_" + datetime.now().strftime('%Y-%m-%d'))
    else:
        st.error("검사과정설명 문서를 찾을 수 없습니다.")

# Add narration download button
if is_valid:
    st.write("---")
    st.subheader("나레이션 mp3 다운로드")
    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        narration_blob = bucket.blob('MT_results/memory test narration 13분.mp3')
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
if is_valid:
    st.subheader("전문가 EGD 수행 해설 동영상 다운로드")
    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        demonstration1_blob = bucket.blob('EGD_variation/B1.mp4')
        if demonstration1_blob.exists():
            demonstration_url = demonstration1_blob.generate_signed_url(expiration=timedelta(minutes=15))
            if st.download_button(
                label="EGD 해설 동영상 1 다운로드",
                data=demonstration1_blob.download_as_bytes(),
                file_name="B1.mp4",
                mime="video/mp4"
            ):
                st.write("")
        else:
            st.error("EGD 해설 동영상 1 파일을 찾을 수 없습니다.")
       
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        demonstration2_blob = bucket.blob('EGD_variation/B2.mp4')
        if demonstration2_blob.exists():
            demonstration2_url = demonstration2_blob.generate_signed_url(expiration=timedelta(minutes=15))
            if st.download_button(
                label="EGD 해설 동영상 2 다운로드",
                data=demonstration2_blob.download_as_bytes(),
                file_name="B2.mp4",
                mime="video/mp4"
            ):
                st.write("")
        else:
            st.error("EGD 해설 동영상 2 파일을 찾을 수 없습니다.")

    except Exception as e:
        st.error(f"EGD 해설 동영상 파일 다운로드 중 오류가 발생했습니다: {e}")

st.write("---")

# File uploader - only show if inputs are valid
uploaded_file = None
if is_valid:
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
            video_file_name = f"{position}_{user_name}{extension}"

            # Firebase Storage upload for video
            bucket = storage.bucket('amcgi-bulletin.appspot.com')
            video_blob = bucket.blob(f"MT_results/MT_results/{video_file_name}")
            video_blob.upload_from_filename(temp_video_path, content_type=uploaded_file.type)

            # Success message
            st.success(f"{video_file_name} 파일이 성공적으로 업로드되었습니다!")
            st.session_state.show_file_list = True
    except Exception as e:
        # Error message
        st.error(f"업로드 중 오류가 발생했습니다: {e}")

# Only show file list after successful upload
if st.session_state.show_file_list:
    st.write("---")
    st.subheader("업로드된 파일 목록")

    try:
        # Get bucket and list files
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        blobs = bucket.list_blobs(prefix="MT_results/")
        
        # Create a list of files
        for blob in blobs:
            if blob.name != "MT_results/":  # Skip the directory itself
                st.write(f" {os.path.basename(blob.name)}")
    except Exception as e:
        st.error(f"파일 목록을 불러오는 중 오류가 발생했습니다: {e}")
