import os
import uuid
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends, status
from fastapi.responses import Response

from app.api.deps import get_current_user
from app.db.models import User as UserModel

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

@router.delete("/{filename}", status_code=status.HTTP_204_NO_CONTENT)
def delete_image(
    filename: str,
    current_user: UserModel = Depends(get_current_user) # 로그인 필수
):
    """
    이미지 삭제 API
    - 서버의 uploads 폴더에서 파일을 영구 삭제합니다.
    - 로그인한 사용자만 호출할 수 있습니다.
    """
    
    # 파일 경로 보안 검사 (Directory Traversal 방지)
    # os.path.basename을 쓰면 경로를 다 떼고 순수 파일명만 남김
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없습니다."
        )
    
    # 파일 삭제
    try:
        os.remove(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 삭제 중 오류가 발생했습니다: {str(e)}"
        )
        
    return Response(status_code=status.HTTP_204_NO_CONTENT)