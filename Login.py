import streamlit as st
import requests
import json
import firebase_admin
from firebase_admin import credentials, db, auth
from datetime import datetime, timezone
import tempfile
import os
from pytz import timezone

# Firebase 초기화 (아직 초기화되지 않은 경우에만)
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
    
    # 데이터베이스 URL이 None이 아닌지 확인
    database_url = st.secrets.get("FIREBASE_DATABASE_URL")
    if not database_url:
        raise ValueError("FIREBASE_DATABASE_URL is not set in Streamlit secrets")
        
    firebase_admin.initialize_app(cred, {
        'databaseURL': database_url,
        'storageBucket': st.secrets.get("FIREBASE_STORAGE_BUCKET")
    })
    
    # Firebase Storage 버킷 초기화
    from firebase_admin import storage
    bucket = storage.bucket()

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
            # 로그인 시작 시간 기록 (한국 시간대 사용)
            login_time = datetime.now(timezone('Asia/Seoul'))
            login_time_str = login_time.strftime("%Y_%m_%d_%H_%M_%S")
            st.session_state['login_time'] = login_time
            
            # Firebase Authentication 성공 후 사용자 정보 가져오기
            user_id = response_data['localId']
            id_token = response_data['idToken']  # ID 토큰 저장
            
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
                
            # 로그인 로그 파일 생성 및 업로드
            login_filename = f"{position}*{name}*login*{login_time_str}"
            login_file_content = f"{position}*{name}*login*{login_time_str}\n"
            
            # 임시 디렉토리에 파일 저장 및 업로드
            with tempfile.TemporaryDirectory() as temp_dir:
                login_file_path = os.path.join(temp_dir, login_filename)
                with open(login_file_path, "w", encoding="utf-8") as file:
                    file.write(login_file_content)
                
                # Firebase Storage에 업로드
                try:
                    login_blob = bucket.blob(f"log_login/{login_filename}")
                    login_blob.upload_from_filename(login_file_path)
                    # 로그아웃 시 삭제하기 위해 경로 저장
                    st.session_state['login_blob_path'] = f"log_login/{login_filename}"
                except Exception as e:
                    st.error(f"로그인 로그 업로드 중 오류 발생: {str(e)}")

            # Supabase로 로그인 기록 추가
            supabase_url = st.secrets["supabase_url"]
            supabase_key = st.secrets["supabase_key"]
            supabase_headers = {
                "Content-Type": "application/json",
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}"
            }

            login_data = {
                "position": position,
                "name": name,
                "time": login_time.isoformat(),
                "event": "login",
                "duration": 0,
                "user_id": user_id
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
            st.session_state['user_name'] = name  # 노트패드 방식과 일치하도록 추가
            st.session_state['user_position'] = position  # 노트패드 방식과 일치하도록 추가
            st.session_state['login_record_id'] = supabase_response.json()[0]['id'] if supabase_response.status_code == 201 else None
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
        # 로그아웃 시간 기록
        logout_time = datetime.now(timezone('Asia/Seoul'))
        logout_time_str = logout_time.strftime("%Y_%m_%d_%H_%M_%S")
        
        # 사용 시간 계산 (분 단위로 환산)
        if 'login_time' in st.session_state:
            login_time = st.session_state['login_time']
            duration_seconds = (logout_time - login_time).total_seconds()
            # 총 분으로 환산 (소수점 버림)
            total_minutes = int(duration_seconds // 60)
            
            # 로그아웃 및 사용 시간 로그 파일 생성
            position = st.session_state['user_position']
            name = st.session_state['user_name']
            
            logout_filename = f"{position}*{name}*logout*{logout_time_str}"
            logout_file_content = f"{position}*{name}*logout*{logout_time_str}\n"
            
            # 현재 시간을 포함한 duration 파일명 생성
            current_time_str = datetime.now(timezone('Asia/Seoul')).strftime("%Y_%m_%d_%H_%M_%S")
            duration_filename = f"{position}*{name}*{total_minutes}*{current_time_str}"
            duration_file_content = f"{position}*{name}*{total_minutes}*{current_time_str}\n"
            
            # 임시 디렉토리에 파일 저장 및 업로드
            with tempfile.TemporaryDirectory() as temp_dir:
                # 로그아웃 로그 파일 저장
                logout_file_path = os.path.join(temp_dir, logout_filename)
                with open(logout_file_path, "w", encoding="utf-8") as file:
                    file.write(logout_file_content)
                
                # 사용 시간 로그 파일 저장
                duration_file_path = os.path.join(temp_dir, duration_filename)
                with open(duration_file_path, "w", encoding="utf-8") as file:
                    file.write(duration_file_content)
                
                # Firebase Storage에 업로드
                try:
                    # 로그아웃 로그 업로드 (임시 저장)
                    logout_blob = bucket.blob(f"log_logout/{logout_filename}")
                    logout_blob.upload_from_filename(logout_file_path)
                    logout_blob_path = f"log_logout/{logout_filename}"
                    
                    # 사용 시간 로그 업로드 - 파일 내용을 파일 이름으로 사용
                    duration_blob = bucket.blob(f"log_duration/{duration_filename}")
                    duration_blob.upload_from_filename(duration_file_path)
                    
                    # 사용 시간 저장 후 로그인/로그아웃 로그 삭제
                    if 'login_blob_path' in st.session_state:
                        login_blob = bucket.blob(st.session_state['login_blob_path'])
                        login_blob.delete()
                    
                    logout_blob = bucket.blob(logout_blob_path)
                    logout_blob.delete()
                except Exception as e:
                    st.error("로그 처리 중 오류가 발생했습니다: " + str(e))
            
            # Supabase 로그인 레코드 업데이트 (duration 추가)
            if st.session_state.get('login_record_id'):
                supabase_url = st.secrets["supabase_url"]
                supabase_key = st.secrets["supabase_key"]
                supabase_headers = {
                    "Content-Type": "application/json",
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}"
                }
                
                # 로그인 레코드 업데이트
                login_record_id = st.session_state.get('login_record_id')
                update_data = {"duration": total_minutes}
                
                requests.patch(
                    f"{supabase_url}/rest/v1/login?id=eq.{login_record_id}", 
                    headers=supabase_headers, 
                    json=update_data
                )
            
            # 로그아웃 이벤트 기록 (Supabase)
            user_id = st.session_state.get('user_id')
            logout_data = {
                "position": position,
                "name": name,
                "time": logout_time.isoformat(),
                "event": "logout",
                "duration": total_minutes,
                "user_id": user_id
            }
            
            # Supabase에 로그아웃 기록 전송
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
