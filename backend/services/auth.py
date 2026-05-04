import jwt
import datetime
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = "frostguard-admin-secret-key-2024"
ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24

security = HTTPBearer()


def create_token(username: str) -> str:
    """Create a JWT token for an admin user."""
    payload = {
        "sub": username,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRY_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_admin(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """FastAPI dependency — extracts and validates admin from JWT Bearer token."""
    return verify_token(credentials.credentials)
