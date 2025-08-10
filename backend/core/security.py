from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

from core.config import settings


def derive_key(password: str, salt: bytes) -> bytes:
    """从密码派生密钥"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())
    return key

def encrypt_token(token: str) -> str:
    """加密Plex令牌"""
    salt = b'salt_'
    key = derive_key(settings.auth.SECRET_KEY, salt)
    
    # 使用固定IV（与Node.js版本保持一致）
    iv = b'\x00' * 16
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    # PKCS7填充
    padding_length = 16 - (len(token) % 16)
    padded_token = token + chr(padding_length) * padding_length
    
    encrypted = encryptor.update(padded_token.encode()) + encryptor.finalize()
    return base64.b64encode(encrypted).decode()

def decrypt_token(encrypted_token: str) -> str:
    """解密Plex令牌"""
    salt = b'salt_'
    key = derive_key(settings.auth.SECRET_KEY, salt)
    
    # 使用固定IV（与Node.js版本保持一致）
    iv = b'\x00' * 16
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    
    encrypted = base64.b64decode(encrypted_token)
    decrypted = decryptor.update(encrypted) + decryptor.finalize()
    
    # 移除PKCS7填充
    padding_length = decrypted[-1]
    return decrypted[:-padding_length].decode()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.auth.SECRET_KEY, algorithm=settings.auth.ALGORITHM)
    return encoded_jwt
