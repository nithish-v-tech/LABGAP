import pytest
from app.security.auth import hash_password, verify_password, create_access_token
import jwt
from app.config import settings

def test_password_hashing():
    pwd = "SecurePassword123!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

def test_jwt_token_generation_and_payload():
    data = {"sub": "admin@labgap.demo", "role": "admin"}
    token = create_access_token(data)
    assert token is not None

    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded["sub"] == "admin@labgap.demo"
    assert decoded["role"] == "admin"
    assert "exp" in decoded
