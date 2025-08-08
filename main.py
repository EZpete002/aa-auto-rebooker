from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from security import verify_shared_secret
from gpt_agent import ask_gpt
from scraper import scrape_passenger_info  # make sure this is async

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
async def rebook(body: RebookBody, authorization: str | None = Header(None)):
    verify_shared_secret(authorization)

    trip_info = await scrape_passenger_info(
        body.recordLocator,
        body.firstName,
        body.lastName,
        body.dobMonth,
        body.dobDay,
        body.dobYear
    )

    gpt_response = ask_gpt(trip_info)
    return {"result": gpt_response}
