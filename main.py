from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from security import verify_shared_secret
from scraper import scrape_passenger_info  # async function

app = FastAPI(title="AA Auto Rebooker (Data Only)")

class LookupBody(BaseModel):
    recordLocator: str
    firstName: str
    lastName: str
    dobMonth: str
    dobDay: str
    dobYear: str

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/lookup")
async def lookup(body: LookupBody, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    # Require bearer token so only your GPT Action can call this
    verify_shared_secret(authorization)
    try:
        data = await scrape_passenger_info(
            body.recordLocator,
            body.firstName,
            body.lastName,
            body.dobMonth,
            body.dobDay,
            body.dobYear
        )
        # Return structured JSON only. No formatting here.
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
