import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def ask_gpt(prompt):
    messages = [
        {"role": "system", "content": "You are an American Airlines rebooking assistant with QIK system knowledge."},
        {"role": "user", "content": prompt}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )

    return response.choices[0].message.content
