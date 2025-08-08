import os
from fastapi import HTTPException

def verify_shared_secret(authorization: str):
    expected = os.getenv("SHARED_SECRET")
    if not expected:
        raise RuntimeError("SHARED_SECRET env var not set")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid bearer token")
