import json
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from prompts import make_prompt

load_dotenv()

import os

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

with Path("data/benchmark.jsonl").open(encoding="utf-8") as file:
    item = json.loads(next(file))

response = client.chat.completions.create(
    model="anthropic/claude-sonnet-5.5",
    messages=[
        {"role": "user", "content": make_prompt(item, "neutral")}
    ],
    max_tokens=20,
)

print("Tatsächlich gemeldetes Modell:", response.model)
print("Antwort:", repr(response.choices[0].message.content))
