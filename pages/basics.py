import streamlit as st
import os
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, storage
import tempfile
from utils.auth import check_login, handle_logout

# Set page to wide mode
st.set_page_config(page_title="Simulation center", layout="wide")

# 로그인 상태 확인
if "logged_in" not in st.session_state or not st.session_state['logged_in']:
    st.warning('로그인이 필요합니다.')
    st.stop()

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

    # 로그아웃 버튼
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    # Title and Instructions
    st.title("Simulation Center EGD basic course orientation")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.markdown("이 페이지는 Simulation center EGD basic course에 대한 orientation 동영상을 시청하는 곳입니다.")
        st.write("simulation center를 이용하기 전에, simulation_center_orientation.mp4 파일을 시청하세요.")
    st.write("---")

    # 세부항목 선택 드롭다운 메뉴 추가
    selected_option = st.selectbox(
        "세부항목 선택",
        ["Sim orientation", "MT", "SHT", "EMT"]
    )

    # 선택된 옵션에 따라 다른 기능 실행
    if selected_option == "Sim orientation":
        # 기존의 orientation 비디오 관련 코드
        st.subheader("Simulation Center EGD basic course orientation 파일 시청")
        try:
            bucket = storage.bucket('amcgi-bulletin.appspot.com')
            sim_blob = bucket.blob('Simulator_training/Sim/simulation_center_orientation.mp4')
            if sim_blob.exists():
                sim_url = sim_blob.generate_signed_url(expiration=timedelta(minutes=15))
                
                # Initialize session state for video player
                if 'show_video' not in st.session_state:
                    st.session_state.show_video = False
                
                # 비디오 플레이어를 위한 placeholder 생성
                video_player_placeholder = st.empty()
                
                # 동영상 시청 버튼
                if st.button("동영상 시청"):
                    # 비디오 표시 상태 토글
                    st.session_state.show_video = not st.session_state.show_video
                    
                    if st.session_state.show_video:
                        # 로그 파일 생성 및 업로드
                        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                            log_content = f"Sim_orientation video watched by {name} ({position}) on {current_date}"
                            temp_file.write(log_content)
                            temp_file_path = temp_file.name

                        # Firebase Storage에 로그 파일 업로드
                        log_blob = bucket.blob(f"Simulator_training/Sim/log_Sim/{position}*{name}*Sim")
                        log_blob.upload_from_filename(temp_file_path)
                        os.unlink(temp_file_path)
                    
                # 비디오 플레이어 표시
                if st.session_state.show_video:
                    # 동영상 플레이어 렌더링
                    with video_player_placeholder.container():
                        video_html = f'''
                        <div style="display: flex; justify-content: center;">
                            <video width="1000" height="800" controls controlsList="nodownload">
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
        
        try:
            bucket = storage.bucket('amcgi-bulletin.appspot.com')
            demonstration1_blob = bucket.blob('EGD_variation/B1.mp4')
            if demonstration1_blob.exists():
                demonstration_url = demonstration1_blob.generate_signed_url(expiration=timedelta(minutes=15))
                
                # 세션 상태 초기화
                if 'show_video' not in st.session_state:
                    st.session_state.show_video = False
                
                # 비디오 플레이어를 위한 placeholder 생성
                video_player_placeholder = st.empty()
                
                # 동영상 시청 버튼
                if st.button("동영상 시청"):
                    # 비디오 표시 상태 토글
                    st.session_state.show_video = not st.session_state.show_video
                    
                    if st.session_state.show_video:
                        # 로그 파일 생성 및 업로드
                        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                            log_content = f"MT_orientation video watched by {name} ({position}) on {current_date}"
                            temp_file.write(log_content)
                            temp_file_path = temp_file.name

                        # Firebase Storage에 로그 파일 업로드
                        log_blob = bucket.blob(f"Simulator_training/MT/log_MT/{position}*{name}*MT")
                        log_blob.upload_from_filename(temp_file_path)
                        os.unlink(temp_file_path)
                    
                # 비디오 플레이어 표시
                if st.session_state.show_video:
                    # 동영상 플레이어 렌더링
                    with video_player_placeholder.container():
                        video_html = f'''
                        <div style="display: flex; justify-content: center;">
                            <video width="1000" height="800" controls controlsList="nodownload">
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

        elif selected_option == "SHT":
            # SHT 관련 코드
            st.subheader("SHT (Scope Handling Training)")
            try:
                bucket = storage.bucket('amcgi-bulletin.appspot.com')
                demonstration_blob = bucket.blob('Simulator_training/SHT/SHT_orientation.mp4')
                if demonstration_blob.exists():
                    demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
                    
                    # 세션 상태 초기화
                    if 'show_video' not in st.session_state:
                        st.session_state.show_video = False
                        
                    # 비디오 플레이어를 위한 placeholder 생성
                    video_player_placeholder = st.empty()
                    
                    # 동영상 시청 버튼
                    if st.button("동영상 시청"):
                        # 비디오 표시 상태 토글
                        st.session_state.show_video = not st.session_state.show_video
                        
                        if st.session_state.show_video:
                            # 로그 파일 생성 및 업로드
                            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                                log_content = f"SHT_orientation video watched by {name} ({position}) on {current_date}"
                                temp_file.write(log_content)
                                temp_file_path = temp_file.name

                            # Firebase Storage에 로그 파일 업로드
                            log_blob = bucket.blob(f"Simulator_training/SHT/log_SHT/{position}*{name}*SHT")
                            log_blob.upload_from_filename(temp_file_path)
                            os.unlink(temp_file_path)
                        
                    # 비디오 플레이어 표시
                    if st.session_state.show_video:
                        # 동영상 플레이어 렌더링
                        with video_player_placeholder.container():
                            video_html = f'''
                            <div style="display: flex; justify-content: center;">
                                <video width="1000" height="800" controls controlsList="nodownload">
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
                        log_file_name = f"{position}*{name}*SHT_result"

                        # Create log file
                        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                            log_content = f"SHT_result video uploaded by {name} ({position}) on {current_date}"
                            temp_file.write(log_content)
                            temp_file_path = temp_file.name

                        # Firebase Storage upload for log file
                        log_blob = bucket.blob(f"Simulator_training/SHT/log_SHT_result/{log_file_name}")
                        log_blob.upload_from_filename(temp_file_path)

                        # Remove temporary log file
                        os.unlink(temp_file_path)

                        # Success message
                        st.success(f"{video_file_name} 파일이 성공적으로 업로드되었습니다!")
                        st.session_state.show_file_list = True
                except Exception as e:
                    # Error message
                    st.error(f"업로드 중 오류가 발생했습니다: {e}")

        elif selected_option == "EMT":
            # EMT 관련 코드
            st.subheader("EMT (Endoscopy Maneuver Training)")
            try:
                bucket = storage.bucket('amcgi-bulletin.appspot.com')
                demonstration_blob = bucket.blob('Simulator_training/EMT/EMT_orientation.mp4')
                if demonstration_blob.exists():
                    demonstration_url = demonstration_blob.generate_signed_url(expiration=timedelta(minutes=15))
                    
                    # 세션 상태 초기화
                    if 'show_video' not in st.session_state:
                        st.session_state.show_video = False
                    
                    # 비디오 플레이어를 위한 placeholder 생성
                    video_player_placeholder = st.empty()
                    
                    # 동영상 시청 버튼
                    if st.button("동영상 시청", key="toggle_video"):
                        # 비디오 표시 상태 토글
                        st.session_state.show_video = not st.session_state.show_video
                        
                        if st.session_state.show_video:
                            # 로그 파일 생성 및 업로드
                            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
                                log_content = f"EMT_orientation video watched by {name} ({position}) on {current_date}"
                                temp_file.write(log_content)
                                temp_file_path = temp_file.name

                            # Firebase Storage에 로그 파일 업로드
                            log_blob = bucket.blob(f"Simulator_training/EMT/log_EMT/{position}*{name}*EMT")
                            log_blob.upload_from_filename(temp_file_path)
                            os.unlink(temp_file_path)
                        
                    # 비디오 플레이어 표시
                    if st.session_state.show_video:
                        # 동영상 플레이어 렌더링
                        with video_player_placeholder.container():
                            video_html = f'''
                            <div style="display: flex; justify-content: center;">
                                <video width="1000" height="800" controls controlsList="nodownload">
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

            uploaded_files = st.file_uploader("분석할 파일들(avi, mp4, bmp)을 탐색기에서 찾아 모두 선택해주세요 단 동영상은 한개만 선택할 수 있습니다.", 
                                            accept_multiple_files=True,
                                            type=['avi', 'bmp', 'mp4'])

            # 파일의 업로드 및 파악
            if uploaded_files:
                st.write(f"총 {len(uploaded_files)}개의 파일이 선택되었습니다.")
                if not name:
                    st.error("이름이 입력되지 않았습니다.")
                else:
                    # 임시 디렉토리 생성
                    temp_dir = "temp_files"
                    os.makedirs(temp_dir, exist_ok=True)

                    # 파일 분류
                    has_bmp = False
                    avi_files = []
                    bmp_files = []

                    # 업로드된 파일 저장 및 분류
                    total_files = len(uploaded_files)
                    for uploaded_file in uploaded_files:
                        temp_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        if uploaded_file.name.endswith('.avi') or uploaded_file.name.endswith('.mp4'):
                            avi_files.append(temp_path)
                        elif uploaded_file.name.endswith('.bmp'):
                            has_bmp = True
                            bmp_files.append(temp_path)

                    st.write(f"avi 파일 수 : {len([file for file in avi_files if file.endswith('.avi')])} , MP4 파일 수 : {len([file for file in avi_files if file.endswith('.mp4')])} , BMP 파일 수: {len(bmp_files)}")

                    # BMP 이미지 수 확인
                    if not (62 <= len(bmp_files) <= 66):
                        st.error("사진의 숫자가 62장에서 66을 벗어납니다. 다시 시도해 주세요")
                        st.stop()

                    # AVI 파일 처리
                    total_avi_files = len(avi_files)
                    for file_path in avi_files:
                        camera = cv2.VideoCapture(file_path)
                        if not camera.isOpened():
                            st.error("동영상 파일을 열 수 없습니다.")
                            continue

                        length = int(camera.get(cv2.CAP_PROP_FRAME_COUNT))
                        frame_rate = camera.get(cv2.CAP_PROP_FPS)
                        duration = length / frame_rate

                        st.write(f"---\n동영상 길이: {int(duration // 60)} 분 {int(duration % 60)} 초")
                        if not (300 <= duration <= 330):
                            st.error("동영상의 길이가 5분에서 5분30초를 벗어납니다. 다시 시도해 주세요")
                            st.stop()

                        st.write(f"비디오 정보 : 총 프레임 수 = {length} , 프레임 레이트 = {frame_rate:.2f}")
                        progress_container = st.empty()
                        progress_container.progress(0)


                        try:
                            # 프레임 처리를 위한 변수 초기화
                            pts = []
                            angle_g = np.array([])
                            distance_g = np.array([])
                            frame_count = 0

                            # 진행률 표시를 위한 컨테이너 생성
                            progress_bar = st.progress(0)
                            progress_text = st.empty()

                            while True:
                                ret, frame = camera.read()
                                if not ret:
                                    break

                                # 프레임 카운트 증가
                                frame_count += 1

                                try:
                                    # 프레임 분석
                                    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                                    
                                    # 색상 범위 설정 및 마스크 생성
                                    green_lower = np.array([35, 80, 50], np.uint8)
                                    green_upper = np.array([60, 255, 255], np.uint8)
                                    green = cv2.inRange(hsv, green_lower, green_upper)

                                    # 윤곽선 검출
                                    contours, hierarchy = cv2.findContours(green, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                                    
                                    if len(contours) > 0:
                                        # 가장 큰 윤곽선 찾기
                                        c = max(contours, key=cv2.contourArea)
                                        ga = cv2.contourArea(c)
                                        
                                        if ga > 500:
                                            u = c
                                            pts.extend([frame_count, 2])
                                        else:
                                            u = np.array([[[0, 0]], [[1, 0]], [[2, 0]], [[2, 1]], [[2, 2]], [[1, 2]], [[0, 2]], [[0, 1]]])
                                            pts.extend([frame_count, 3])

                                        # 중심점 계산
                                        M = cv2.moments(u)
                                        if M["m00"] != 0:
                                            px = abs(int(M["m10"] / M["m00"]))
                                            py = abs(int(M["m01"] / M["m00"]))
                                        else:
                                            px, py = 0, 0

                                        pts.extend([px, py])

                                        # 최소 외접원 계산
                                        ((cx, cy), radius) = cv2.minEnclosingCircle(u)
                                        pts.append(int(radius))

                                    # 진행률 업데이트 (5프레임마다)
                                    if frame_count % 5 == 0:
                                        progress = frame_count / length
                                        progress_container.progress(progress)

                                except Exception as e:
                                    st.write(f"\n[ERROR] 프레임 {frame_count} 처리 중 오류 발생 : {str(e)}")
                                    continue

                            # 진행률 표시 컨테이너 제거
                            progress_bar.empty()
                            progress_text.empty()

                            st.write(f"처리된 총 프레임 수 :  {frame_count}")
                            st.write(f"수집된 데이터 포인트 수 : {len(pts)}")
                            st.write("\n-> 분석 완료")

                        except Exception as e:
                            st.write(f"\n[ERROR] 비디오 처리 중 치명적 오류 발생 : {str(e)}")
                        finally:
                            # 분석 완료 후 정리
                            camera.release()

                        k = list(pts)
                        array_k = np.array(k)

                        frame_no = array_k[0::5]
                        timesteps = len(frame_no)
                        frame_no2 = np.reshape(frame_no, (timesteps, 1))

                        color = array_k[1::5]
                        color2 = np.reshape(color, (timesteps, 1))

                        x_value = array_k[2::5]
                        x_value2 = np.reshape(x_value, (timesteps, 1))

                        y_value = array_k[3::5]
                        y_value2 = np.reshape(y_value, (timesteps, 1))

                        radius2 = array_k[4::5]
                        radius3 = np.reshape(radius2, (timesteps, 1))

                        points = np.hstack([frame_no2, color2, x_value2, y_value2, radius3])

                        for i in range(timesteps - 1):
                            if (points[i][1] != 3 and points[i + 1][1] != 3) and (points[i][1] == 2 and points[i + 1][1] == 2):
                                a = points[i + 1][2] - points[i][2]
                                b = points[i + 1][3] - points[i][3]
                                angle_g = np.append(angle_g, degrees(atan2(a, b)))
                                rr = points[i][4]
                                delta_g = (np.sqrt((a * a) + (b * b))) / rr
                                distance_g = np.append(distance_g, delta_g)
                            else:
                                distance_g = np.append(distance_g, 0)

                        mean_g = np.mean([ggg for ggg in distance_g if ggg < 6])
                        std_g = np.std([ggg for ggg in distance_g if ggg < 6])
                        x_test = np.array([[mean_g, std_g]])

                        # 결과의 일관성을 위해 랜덤 시드 설정
                        np.random.seed(42)
                        
                        # 기존 훈련 데이터 로드
                        x_train = np.loadtxt('x_train.csv', delimiter=',')

                        # 고정된 정규화 범위 사용
                        scaler = MinMaxScaler(feature_range=(0, 1))
                        x_train_scaled = scaler.fit_transform(x_train)
                        x_test_scaled = scaler.transform(x_test)

                        # SVM 모델 생성
                        clf = svm.OneClassSVM(nu=0.1, kernel="rbf", gamma=0.1)
                        clf.fit(x_train_scaled)

                        st.write("---")
                        st.subheader("최종 판정")

                        y_pred_test = clf.predict(x_test_scaled)
                        str4 = str(round(clf.decision_function(x_test_scaled)[0], 4))
                        st.write(f"판단 점수: {str4}")
                        if y_pred_test == 1:
                            str3 = 'Pass'
                            st.write('EGD 수행이 적절하게 진행되어 EMT 과정에서 합격하셨습니다. 수고하셨습니다.')
                        else:
                            str3 = 'Fail.'
                            st.write('EGD 수행이 적절하게 진행되지 못해 불합격입니다. 다시 도전해 주세요.')


                    # BMP 파일 처리 (한 번만 실행)
                    if has_bmp and duration is not None:
                        # A4 크기 설정 (300 DPI 기준)
                        a4_width = 2480
                        a4_height = 3508
                        images_per_row = 8
                        padding = 20

                        # A4 크기의 빈 이미지 생성
                        result_image = Image.new('RGB', (a4_width, a4_height), 'white')
                        draw = ImageDraw.Draw(result_image)

                        # 각 이미지의 크기 계산
                        single_width = (a4_width - (padding * (images_per_row + 1))) // images_per_row

                        # 이미지 배치
                        x, y = padding, padding
                        for idx, bmp_file in enumerate(bmp_files):
                            img = Image.open(bmp_file)
                            img.thumbnail((single_width, single_width))
                            result_image.paste(img, (x, y))
                            
                            x += single_width + padding
                            if (idx + 1) % images_per_row == 0:
                                x = padding
                                y += single_width + padding
                        
                        # 텍스트 추가
                        font_size = 70  # 폰트 크기를 100으로 수정
                        text_color = (0, 0, 0)  # 검은색

                        try:
                            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # 볼드체 폰트 경로
                            font = ImageFont.truetype(font_path, font_size)
                        except OSError:
                            try:
                                font_path = "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"  # 볼드체 폰트 경로
                                font = ImageFont.truetype(font_path, font_size)
                            except OSError:
                                # Windows 시스템 폰트 경로 시도
                                try:
                                    font_path = "C:/Windows/Fonts/malgun.ttf"  # Windows의 맑은 고딕 폰트
                                    font = ImageFont.truetype(font_path, font_size)
                                except OSError:
                                    font = ImageFont.load_default()
                                    st.write("시스템 폰트를 찾을 수 없어 기본 폰트를 사용합니다.")

                        # 동영상 길이 저장
                        video_length = f"{int(duration // 60)} min {int(duration % 60)} sec"

                        # 추가할 텍스트
                        text = f"Photo number: {len(bmp_files)}\nDuration: {video_length}\nResult: {str3}\nSVM_value: {str4}"

                        # 텍스트 크기 계산
                        text_bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = text_bbox[2] - text_bbox[0]
                        text_height = text_bbox[3] - text_bbox[1]

                        # 텍스트 위치 계산 (왼쪽 정렬, 맨 아래 줄)
                        x = padding  # 왼쪽 정렬
                        y = a4_height - text_height - padding * 2  # 여백을 더 확보

                        # 텍스트 그리기
                        draw.text((x, y), text, fill=text_color, font=font, align="left")
                        st.divider()
                        st.subheader("이미지 전송 과정")
                        
                        # 임시 디렉토리 생성
                        os.makedirs('Simulator_training/EMT/EMT_result/', exist_ok=True)
                        os.makedirs('Simulator_training/EMT/log_EMT_result/', exist_ok=True)
                        
                        # 결과 이미지 크기 조정
                        width, height = result_image.size
                        result_image = result_image.resize((width // 2, height // 2), Image.Resampling.LANCZOS)
                        
                        # 결과 이미지 저장 - 하이픈(-)을 구분자로 사용
                        temp_image_path = f'Simulator_training/EMT/EMT_result/{position}-{name}-EMT_result.png'
                        result_image.save(temp_image_path, format='PNG')
                        
                        try:
                            if str3 == "Pass":
                                # Firebase Storage에 업로드
                                firebase_path = f'Simulator_training/EMT/EMT_result/{position}-{name}-EMT_result.png'
                                result_blob = bucket.blob(firebase_path)
                                result_blob.upload_from_filename(temp_image_path, content_type='image/png')
                                st.success(f"이미지가 성공적으로 전송되었습니다.")
                            else:
                                st.warning("평가 결과가 'fail'이므로 업로드하지 않습니다.")
                            
                            st.image(temp_image_path, use_container_width=True)
                            
                            # 로그 파일 생성
                            log_text = f"EMT_result image uploaded by {name} ({position}) on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                            log_file_path = f'Simulator_training/EMT/log_EMT_result/{position}*{name}*EMT_result'
                            with open(log_file_path, 'w') as f:
                                f.write(log_text)
                            log_blob = bucket.blob(f'Simulator_training/EMT/log_EMT_result/{position}*{name}*EMT_result')
                            log_blob.upload_from_filename(log_file_path)
                        except Exception as e:
                            st.error(f"전송 도중 오류 발생: {str(e)}")
                        finally:
                            # 임시 파일 삭제
                            if os.path.exists(temp_image_path):
                                os.remove(temp_image_path)
                            if os.path.exists(log_file_path):
                                os.remove(log_file_path)
                                
                st.divider() 
                st.success("평가가 완료되었습니다.")
                
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")
            st.stop()  # 치명적 오류 시 실행 중단

    else:
        st.warning('Please log in to read more.')