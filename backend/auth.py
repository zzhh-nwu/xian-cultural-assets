"""
认证模块 — JWT Token + 密码哈希
"""

import hashlib
import hmac
import json
import time
import os

try:
    from database import get_db
except ImportError:
    from backend.database import get_db

SECRET_KEY = os.environ.get('JWT_SECRET', 'xian-culture-platform-secret-key-2026')
TOKEN_EXPIRE = 7 * 24 * 3600  # 7天


def hash_password(password: str) -> str:
    """SHA256 哈希密码"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return hash_password(password) == hashed


def base64url_encode(data: bytes) -> str:
    """Base64URL 编码"""
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


def base64url_decode(s: str) -> bytes:
    """Base64URL 解码"""
    import base64
    padding = 4 - len(s) % 4
    if padding != 4:
        s += '=' * padding
    return base64.urlsafe_b64decode(s)


def create_token(user_id: int, username: str, role: str) -> str:
    """生成 JWT token"""
    header = base64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = base64url_encode(json.dumps({
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": int(time.time()) + TOKEN_EXPIRE,
    }).encode())
    signature = base64url_encode(
        hmac.new(SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
    )
    return f"{header}.{payload}.{signature}"


def verify_token(token: str) -> dict | None:
    """验证 JWT token，返回 payload 或 None"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header, payload, signature = parts
        expected_sig = base64url_encode(
            hmac.new(SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()
        )
        if signature != expected_sig:
            return None
        data = json.loads(base64url_decode(payload))
        if data.get('exp', 0) < time.time():
            return None
        return data
    except Exception:
        return None


def get_user_by_id(user_id: int) -> dict | None:
    """根据ID获取用户"""
    db = get_db()
    row = db.execute("SELECT id, username, email, role, avatar, created_at FROM users WHERE id=?", (user_id,)).fetchone()
    db.close()
    if row:
        return dict(row)
    return None


def get_user_by_username(username: str) -> dict | None:
    """根据用户名获取用户（含密码）"""
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    db.close()
    if row:
        return dict(row)
    return None
