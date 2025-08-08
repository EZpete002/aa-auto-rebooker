from fastapi import FastAPI
from pydantic import BaseModel
from scraper import scrape_passenger_info
from gpt_agent import ask_gpt

app = FastAPI()

class RebookRequest(BaseModel):
    recordLocator: str
    firstName: str
    lastName: str
    dobMonth: str
    dobDay: str
    dobYear: str

@app.post("/rebook")
async def rebook(request: RebookRequest):
    trip_info = await scrape_passenger_info(
        request.recordLocator,
        request.firstName,
        request.lastName,
        request.dobMonth,
        request.dobDay,
        request.dobYear,
    )
    gpt_response = ask_gpt(trip_info)
    return {"result": gpt_response}
