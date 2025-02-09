from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ...utils.security import decode_access_token
from ...config.settings import API_V1_PREFIX

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/{API_V1_PREFIX}/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return payload  # Contains user details