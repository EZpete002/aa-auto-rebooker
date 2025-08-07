import os
from dotenv import load_dotenv
import openai

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")
if not ASSISTANT_ID:
    raise RuntimeError("ASSISTANT_ID is not set")

openai.api_key = OPENAI_API_KEY

def ask_gpt(trip_info: str) -> str:
    # Create a new thread for each query
    thread = openai.beta.threads.create()
    
    # Add the trip info as a message
    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=f"Here’s the latest scraped reservation info:\n\n{trip_info}"
    )
    
    # Run the Assistant
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )
    
    # Poll until it’s complete
    while True:
        run_status = openai.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )
        if run_status.status in ["completed", "failed", "cancelled"]:
            break
    
    # Get messages
    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value
