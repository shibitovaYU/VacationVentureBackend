from typing import Optional

from fastapi import Header, HTTPException
from firebase_admin import auth


def get_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    return parts[1].strip()


async def get_current_uid(authorization: Optional[str] = Header(default=None)) -> str:
    token = get_bearer_token(authorization)
    try:
        decoded = auth.verify_id_token(token)
        uid = decoded.get("uid")
        if not uid:
            raise HTTPException(status_code=401, detail="Token decoded but uid missing")
        return uid
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
