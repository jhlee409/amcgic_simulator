import streamlit as st
import requests
import json
import firebase_admin
from firebase_admin import credentials, db, auth, storage
from datetime import datetime, timezone
import tempfile
import os

# Firebase 초기화 (아직 초기화되지 않은 경우에만)
if not firebase_admin._apps:

    # Streamlit Secrets에서 Firebase 설정 정보 로드
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
    
    # 데이터베이스 URL이 None이 아닌지 확인
    database_url = st.secrets.get("FIREBASE_DATABASE_URL")
    if not database_url:
        raise ValueError("FIREBASE_DATABASE_URL is not set in Streamlit secrets")
        
    # Firebase 스토리지 버킷 이름 가져오기
    storage_bucket = "amcgi-bulletin.appspot.com"
        
    firebase_admin.initialize_app(cred, {
        'databaseURL': database_url,
        'storageBucket': storage_bucket
    })

st.set_page_config(page_title="amcgic_simulator")

# Streamlit 페이지 설정
st.title("AMC GI 상부 Simulator training")
st.header("Login page")
with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
    st.write("이 게시판은 서울 아산병원 GI 상부 전용 게시판입니다.")
    st.write("GI 상부의 simulattor training 관련 자료를 제곻하고 결과를 업로드하기 위한 페이지 입니다.")
    st.write("한글 이름은 게시판에 접속하셨는지 확인하는 자료이므로 반드시 기입해 주세요.")

st.divider()

# 한글 이름 확인 함수
def is_korean_name(name):
    return any('\u3131' <= char <= '\u3163' or '\uac00' <= char <= '\ud7a3' for char in name)

# 사용자 인풋
email = st.text_input("Email")
password = st.text_input("Password", type="password")
name = st.text_input("Name")  # 이름 입력 필드 추가
position = st.selectbox("Select Position", ["", "Staff", "F1", "F2", "R3", "Student", "신촌", "계명"])  # 직책 선택 필드 추가

# 로그인 버튼 클릭 전 초기화
login_disabled = True  # 초기값 설정

# 유효성 검사 및 로그인 버튼
if st.button("입력 확인"):  # 버튼 이름을 변경하여 ID 충돌 방지
    # 모든 조건이 충족되면 login_disabled를 False로 설정
    if (email != "" and 
        password != "" and 
        position != "" and 
        name != "" and 
        is_korean_name(name)):
        login_disabled = False
        st.success("입력이 확인되었습니다. 로그인 버튼을 클릭해주세요.")
    else:
        login_disabled = True
        if email == "":
            st.error("이메일을 입력해 주세요")
        if password == "":
            st.error("비밀번호를 입력해 주세요")
        if position == "":
            st.error("position을 선택해 주세요")
        if name == "":
            st.error("한글 이름을 입력해 주세요")
        elif not is_korean_name(name):
            st.error("한글 이름을 입력해 주세요")

def handle_login(email, password, name, position):
    try:
        # Streamlit secret에서 Firebase API 키 가져오기
        api_key = st.secrets["FIREBASE_API_KEY"]
        request_ref = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = json.dumps({"email": email, "password": password, "returnSecureToken": True})

        response = requests.post(request_ref, headers=headers, data=data)
        response_data = response.json()

        if response.status_code == 200:
            # Firebase Authentication 성공 후 사용자 정보 가져오기
            user_id = response_data['localId']
            id_token = response_data['idToken']  # ID 토큰 저장
            
            # 현재 시간 가져오기 (초까지)
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 로그인 로그 파일 이름 생성 (position_name_login_시간)
            log_filename = f"{position}_{name}_login_{current_time}.txt"
            
            # 임시 파일 생성
            with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
                temp_file.write(f"Position: {position}\n")
                temp_file.write(f"Name: {name}\n")
                temp_file.write(f"Login Time: {current_time}\n")
                temp_file_path = temp_file.name
            
            try:
                # Firebase Storage에 파일 업로드
                bucket = storage.bucket()
                blob = bucket.blob(f"log_login/{current_time}")
                blob.upload_from_filename(temp_file_path)
                
                # 임시 파일 삭제
                os.unlink(temp_file_path)
                
                # 로그 업로드 성공 메시지 (디버깅용, 필요시 주석 처리)
                # st.success("로그인 로그가 저장되었습니다.")
            except Exception as e:
                st.error(f"로그인 로그 업로드 중 오류 발생: {str(e)}")
            
            # Authentication 사용자 정보 업데이트
            try:
                user = auth.update_user(
                    user_id,
                    display_name=name,
                    custom_claims={'position': position}
                )
            except auth.UserNotFoundError:
                # 사용자가 없는 경우, 새로운 사용자 생성
                try:
                    user = auth.create_user(
                        uid=user_id,
                        email=email,
                        password=password,
                        display_name=name
                    )
                    # 생성된 사용자에 대한 custom claims 설정
                    auth.set_custom_user_claims(user_id, {'position': position})
                    st.success("새로운 사용자가 생성되었습니다.")
                except Exception as e:
                    st.error(f"사용자 생성 중 오류 발생: {str(e)}")
                    return
            
            # Realtime Database에도 정보 저장
            user_ref = db.reference(f'users/{user_id}')
            user_data = user_ref.get()

            if user_data is None:
                # 새 사용자인 경우 정보 저장
                user_ref.set({
                    'email': email,
                    'name': name,
                    'position': position,
                    'created_at': {'.sv': 'timestamp'}  # 서버 타임스탬프 사용
                })
                user_data = {'name': name, 'position': position}
            
            # position이 없는 경우 업데이트
            elif 'position' not in user_data:
                user_ref.update({
                    'position': position
                })
                user_data['position'] = position

            # Supabase로 로그인 기록 추가
            supabase_url = st.secrets["supabase_url"]
            supabase_key = st.secrets["supabase_key"]
            supabase_headers = {
                "Content-Type": "application/json",
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}"
            }

            login_time = datetime.now(timezone.utc)
            st.session_state['login_time'] = login_time.astimezone()  # Update login_time to be timezone-aware
            login_data = {
                "position": position,
                "name": name,
                "time": login_time.isoformat(),
                "event": "login",
                "duration": 0
            }

            supabase_response = requests.post(f"{supabase_url}/rest/v1/login", headers=supabase_headers, json=login_data)

            if supabase_response.status_code == 201:
                st.success(f"환영합니다, {user_data.get('name', email)}님! ({user_data.get('position', '직책 미지정')})")
            else:
                st.error(f"Supabase에 로그인 기록을 추가하는 중 오류 발생: {supabase_response.text}")

            st.session_state['logged_in'] = True
            st.session_state['user_email'] = email
            st.session_state['name'] = name
            st.session_state['position'] = position
            st.session_state['user_id'] = user_id
        else:
            st.error(response_data["error"]["message"])
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# 로그인 버튼
if st.button("Login", disabled=login_disabled):  # 원래 버튼 유지
    handle_login(email, password, name, position)

# 로그 아웃 버튼
if "logged_in" in st.session_state and st.session_state['logged_in']:
    
    # 로그인된 사용자 정보 표시
    st.sidebar.write(f"**사용자**: {st.session_state.get('name', '이름 없음')}")
    st.sidebar.write(f"**직책**: {st.session_state.get('position', '직책 미지정')}")
    
    if st.sidebar.button("Logout"):
        try:
            # 현재 시간 가져오기
            logout_time = datetime.now(timezone.utc)
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Firebase Storage에서 로그인 로그 가져오기
            bucket = storage.bucket()
            login_blobs = list(bucket.list_blobs(prefix='log_login/'))
            logout_blobs = list(bucket.list_blobs(prefix='log_logout/'))
            
            if login_blobs:
                # 가장 최근 로그인 시간 찾기
                latest_login_blob = max(login_blobs, key=lambda x: x.name)
                login_time_str = latest_login_blob.name.split('/')[-1]
                login_time = datetime.strptime(login_time_str, "%Y%m%d_%H%M%S")
                
                # 시간 차이 계산 (초 단위)
                time_duration = int((logout_time - login_time.replace(tzinfo=timezone.utc)).total_seconds())
                
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

                # Supabase에 로그아웃 기록 전송
                logout_data = {
                    "position": position,
                    "name": name,
                    "time": logout_time.isoformat(),
                    "event": "logout",
                    "duration": time_duration
                }
                
                # Supabase 로그아웃 기록
                supabase_url = st.secrets["supabase_url"]
                supabase_key = st.secrets["supabase_key"]
                supabase_headers = {
                    "Content-Type": "application/json",
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}"
                }
                
                requests.post(f"{supabase_url}/rest/v1/login", headers=supabase_headers, json=logout_data)
                
                st.session_state.clear()
                st.success("로그아웃 되었습니다.")
                
            else:
                st.error("로그인 기록을 찾을 수 없습니다.")
                
        except Exception as e:
            st.error(f"로그아웃 처리 중 오류가 발생했습니다: {str(e)}")
