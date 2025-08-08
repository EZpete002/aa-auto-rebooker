# main.py
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json

from security import verify_shared_secret
from gpt_agent import ask_gpt
from scraper import scrape_passenger_info  # async function

app = FastAPI(title="AA Auto Rebooker")

class RebookBody(BaseModel):
    recordLocator: str
    firstName: str
    lastName: str
    dobMonth: str
    dobDay: str
    dobYear: str

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/rebook")
async def rebook(body: RebookBody, authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    # Basic bearer auth so only your GPT Action or trusted client can call this
    verify_shared_secret(authorization)

    try:
        # 1. Scrape live reservation data
        trip_dict = await scrape_passenger_info(
            body.recordLocator,
            body.firstName,
            body.lastName,
            body.dobMonth,
            body.dobDay,
            body.dobYear
        )

        # 2. Serialize dict to JSON text for GPT
        trip_json_text = json.dumps(trip_dict, ensure_ascii=False)

        # 3. Ask your custom GPT for QIK steps based on this JSON
        gpt_response = ask_gpt(trip_json_text)

        # 4. Return both the GPT answer and the parsed data
        return {
            "result": gpt_response,
            "data": trip_dict
        }

    except HTTPException:
        # Re-raise FastAPI HTTP exceptions as is
        raise
    except Exception as e:
        # Surface clean error to client
        raise HTTPException(status_code=500, detail=str(e))
