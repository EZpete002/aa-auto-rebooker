from fastapi import FastAPI, Request
from scraper import scrape_passenger_info
from gpt_agent import ask_gpt

app = FastAPI()

@app.post("/rebook")
async def rebook_passenger(request: Request):
    data = await request.json()
    record_locator = data["recordLocator"]
    last_name = data["lastName"]

    trip_info = scrape_passenger_info(record_locator, last_name)
    gpt_response = ask_gpt(trip_info)

    return {"result": gpt_response}
