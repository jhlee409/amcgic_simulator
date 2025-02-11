from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import firebase_admin
from firebase_admin import credentials, storage
import io
import asyncio
from typing import Generator

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firebase 초기화
def initialize_firebase():
    """Firebase 초기화 함수"""
    if not firebase_admin._apps:
        import streamlit as st
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

def get_chunk_generator(blob) -> Generator[bytes, None, None]:
    """동영상을 청크 단위로 스트리밍하는 제너레이터"""
    buffer = io.BytesIO()
    blob.download_to_file(buffer)
    buffer.seek(0)
    
    chunk_size = 1024 * 1024  # 1MB 청크
    while True:
        chunk = buffer.read(chunk_size)
        if not chunk:
            break
        yield chunk
    buffer.close()

@app.get("/stream/{video_path:path}")
async def stream_video(video_path: str):
    """동영상 스트리밍 엔드포인트"""
    try:
        initialize_firebase()
        bucket = storage.bucket()
        blob = bucket.blob(video_path)
        
        if not blob.exists():
            return Response(content="Video not found", status_code=404)
        
        # 동영상 메타데이터
        content_type = "video/mp4"
        content_length = blob.size
        
        # 스트리밍 응답 생성
        headers = {
            "Content-Type": content_type,
            "Content-Length": str(content_length),
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        
        return StreamingResponse(
            get_chunk_generator(blob),
            headers=headers,
            media_type=content_type
        )
    except Exception as e:
        return Response(content=str(e), status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
