import os
import uuid
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, Request

router = APIRouter()

UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
    
@router.post("/", status_code=201)
async def upload_image(
    request: Request,
    file: UploadFile = File(...)
):
    """
    이미지 업로드 API
    - 파일을 받아 서버에 저장하고, 접근 가능한 URL을 반환합니다.
    """
    
    # 파일명 생성 (중복 방지)
    filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # 비동기 처리
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            # 파일 읽어서 저장
            content = await file.read()
            await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail="이미지 저장 중 오류가 발생했습니다.")
    
    # 접근 가능한 URL 생성
    # request.base_url: 현재 서버의 주소 가져옴.
    file_url = f"{request.base_url}uploads/{filename}"
    
    return {"url": file_url}