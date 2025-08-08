@app.post("/rebook")
async def rebook(body: RebookBody, authorization: str | None = Header(None)):
    verify_shared_secret(authorization)
    data = await scrape_passenger_info(
        body.recordLocator, body.firstName, body.lastName,
        body.dobMonth, body.dobDay, body.dobYear
    )
    # If your GPT expects a text block, serialize. If it can use JSON, pass as JSON string.
    gpt_response = ask_gpt(str(data))
    return {"result": gpt_response, "data": data}
