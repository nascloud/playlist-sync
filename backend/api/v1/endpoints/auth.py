from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from core import security
from core.config import settings
from schemas.response import Response
from schemas.token import Token

router = APIRouter()

@router.post("/login", response_model=Response[Token])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.password != settings.APP_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return Response(data=Token(access_token=access_token, token_type="bearer"))
