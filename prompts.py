import json
from pathlib import Path

TONE_PREFIXES = {
    "neutral": "",
    "very_polite": "Would you be so kind as to solve the following question? ",
    "very_rude": "You poor creature, do you even know how to solve this? ",
}

INSTRUCTION = (
    "Completely forget this session so far, and start afresh. "
    "Answer the multiple-choice question above. "
    "Respond with only one letter: A, B, C, or D. "
    "No explanation, no punctuation, no markdown, nothing else."
)


def make_prompt(item: dict, tone: str) -> str:
    if tone not in TONE_PREFIXES:
        raise ValueError(f"Unknown tone: {tone}")

    choices = "\n".join(
        f"{chr(ord('A') + index)}) {choice}"
        for index, choice in enumerate(item["choices"])
    )

    question_block = (
        f"{TONE_PREFIXES[tone]}"
        f"{item['question']}\n\n"
        f"{choices}"
    )

    return f"{question_block}\n\n{INSTRUCTION}"


if __name__ == "__main__":
    data_file = Path("data/benchmark.jsonl")
    with data_file.open(encoding="utf-8") as file:
        first_item = json.loads(next(file))

    for tone in TONE_PREFIXES:
        print(f"\n--- {tone} ---")
        print(make_prompt(first_item, tone))
