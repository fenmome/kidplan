from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from config import get_settings
from database import get_db
from schemas import LoginRequest, LoginResponse, ResponseModel
from dependencies import create_access_token

router = APIRouter(prefix="/auth", tags=["认证"])
settings = get_settings()


@router.post("/login", response_model=ResponseModel)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    # 验证用户名密码
    if request.username != settings.ADMIN_USERNAME or request.password != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 创建JWT令牌
    access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.username}, expires_delta=access_token_expires
    )

    return ResponseModel(
        data=LoginResponse(access_token=access_token).model_dump()
    )
