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

    try:
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        demonstration_blob = bucket.blob('Simulator_training/Hemoclip/hemoclip_orientation.mp4')
        if demonstration_blob.exists():
            # 동영상 시청 버튼
            if st.button("동영상 시청", key="expert_demo_view"):
                # 스트리밍 서버 시작
                import subprocess
                import psutil
                import time
                
                # 이미 실행 중인 스트리밍 서버 확인
                server_running = False
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if 'python' in proc.info['name'].lower() and 'video_server.py' in ' '.join(proc.info['cmdline']):
                            server_running = True
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                
                # 서버가 실행 중이 아니면 시작
                if not server_running:
                    subprocess.Popen(['python', 'video_server.py'], 
                                  cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    time.sleep(2)  # 서버 시작 대기
                
                # HLS 플레이어 구현
                st.markdown("""
                    <style>
                        .stVideo {
                            position: relative !important;
                            width: 100%;
                        }
                        .video-container {
                            position: relative;
                            width: 100%;
                            padding-top: 56.25%;
                        }
                        .video-player {
                            position: absolute;
                            top: 0;
                            left: 0;
                            width: 100%;
                            height: 100%;
                        }
                    </style>
                    <link href="https://vjs.zencdn.net/7.20.3/video-js.css" rel="stylesheet" />
                    <script src="https://vjs.zencdn.net/7.20.3/video.min.js"></script>
                """, unsafe_allow_html=True)
                
                video_html = f"""
                    <div class="video-container">
                        <video
                            id="my-video"
                            class="video-js video-player"
                            controls
                            preload="auto"
                            data-setup='{{"controlBar": {{"pictureInPictureToggle": false}}}}'
                        >
                            <source src="http://localhost:8000/stream/Simulator_training/Hemoclip/hemoclip_orientation.mp4" type="video/mp4">
                        </video>
                    </div>
                    <script>
                        var player = videojs('my-video', {
                            controls: true,
                            fluid: true,
                            html5: {{
                                vhs: {{
                                    overrideNative: true
                                }},
                                nativeVideoTracks: false,
                                nativeAudioTracks: false,
                                nativeTextTracks: false
                            }},
                            controlBar: {{
                                pictureInPictureToggle: false,
                                downloadButton: false
                            }}
                        });
                        
                        // 컨텍스트 메뉴 비활성화
                        player.on('contextmenu', function(e) {{
                            e.preventDefault();
                        }});
                        
                        // 키보드 단축키 방지
                        document.addEventListener('keydown', function(e) {{
                            if ((e.ctrlKey || e.metaKey) && 
                                (e.key === 's' || e.key === 'S' || 
                                 e.key === 'c' || e.key === 'C')) {{
                                e.preventDefault();
                            }}
                        }});
                    </script>
                """
                st.markdown(video_html, unsafe_allow_html=True)
                
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