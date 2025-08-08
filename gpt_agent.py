# gpt_agent.py
import os
import time
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set")
if not ASSISTANT_ID:
    raise RuntimeError("ASSISTANT_ID is not set")

# New v1.x client pattern
client = OpenAI(api_key=OPENAI_API_KEY)

def _extract_text_from_message(msg) -> str:
    """
    Assistant messages can contain multiple 'content' parts.
    Prefer text parts; join if there are several.
    """
    try:
        parts = []
        for part in msg.content:
            if getattr(part, "type", None) == "text":
                parts.append(part.text.value)
            elif hasattr(part, "text") and hasattr(part.text, "value"):
                parts.append(part.text.value)
        text = "\n".join([p for p in parts if p])
        return text or "No text content found in assistant message."
    except Exception:
        # Last-resort stringify
        return str(getattr(msg, "content", "")) or "No response from assistant."

def ask_gpt(trip_info: str) -> str:
    """
    Sends the scraped reservation (as JSON text or a concise string) to your
    custom Assistant (AAAI) and returns the assistant's reply as plain text.
    """
    # 1) Create a fresh thread
    thread = client.beta.threads.create()

    # 2) Post the user message (trip info)
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=(
            "Analyze the following live reservation data and return a short, "
            "numbered list of QIK steps to rebook or assist the passenger.\n\n"
            f"{trip_info}"
        ),
    )

    # 3) Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID,
    )

    # 4) Poll until the run completes (or fails)
    terminal_states = {"completed", "failed", "cancelled", "expired"}
    while True:
        status = client.beta.threads.runs.retrieve(
            thread_id=thread.id, run_id=run.id
        ).status
        if status in terminal_states:
            break
        time.sleep(0.8)

    if status != "completed":
        return f"Assistant run ended with status: {status}"

    # 5) Get the latest assistant message in the thread
    msgs = client.beta.threads.messages.list(thread_id=thread.id)
    for m in msgs.data:
        if m.role == "assistant":
            return _extract_text_from_message(m)

    return "No response from assistant."
