import os
from dotenv import load_dotenv
import openai
import time

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")
if not ASSISTANT_ID:
    raise RuntimeError("ASSISTANT_ID is not set")

openai.api_key = OPENAI_API_KEY

def ask_gpt(trip_info: str) -> str:
    # Create a new thread
    thread = openai.beta.threads.create()

    # Add the reservation data
    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Here’s the latest scraped reservation info:\n\n{trip_info}"
    )

    # Start a run with your custom assistant
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    # Poll until done
    while True:
        run_status = openai.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run_status.status in ["completed", "failed", "cancelled"]:
            break
        time.sleep(1)

    # Get the latest assistant message
    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    for m in messages.data:
        if m.role == "assistant":
            return m.content[0].text.value

    return "No response from assistant."
