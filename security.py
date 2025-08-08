import os
from fastapi import HTTPException

SHARED_SECRET = os.getenv("SHARED_SECRET")

def verify_shared_secret(authorization: str | None):
    if not SHARED_SECRET:
        return
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != SHARED_SECRET:
        raise HTTPException(status_code=403, detail="Invalid Authorization")
