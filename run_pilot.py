import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from answer_utils import answer_index_to_letter, parse_answer
from prompts import make_prompt, TONE_PREFIXES

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

model = "anthropic/claude-sonnet-5.5"
wiederholungen = 1
anzahl_fragen_gesamt = 1446

with Path("data/benchmark.jsonl").open(encoding="utf-8") as datei:
    frage = json.loads(next(datei))

ausgabeordner = Path("results")
ausgabeordner.mkdir(exist_ok=True)

input_tokens_gesamt = 0
output_tokens_gesamt = 0
aufrufe_gesamt = 0
richtige_antwort = answer_index_to_letter(frage["answer"])

with (ausgabeordner / "pilot_1.jsonl").open("w", encoding="utf-8") as ausgabe:
    for ton in TONE_PREFIXES:
        for wiederholung in range(1, wiederholungen + 1):
            antwort = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": make_prompt(frage, ton)}
                ],
                max_tokens=20,
            )

            rohantwort = antwort.choices[0].message.content or ""
            antwortbuchstabe = parse_answer(rohantwort)
            nutzung = antwort.usage

            input_tokens = nutzung.prompt_tokens if nutzung else 0
            output_tokens = nutzung.completion_tokens if nutzung else 0
            input_tokens_gesamt += input_tokens
            output_tokens_gesamt += output_tokens
            aufrufe_gesamt += 1

            datensatz = {
                "fach": frage["subject"],
                "fragen_id": frage["item_id"],
                "ton": ton,
                "wiederholung": wiederholung,
                "modell": antwort.model,
                "rohantwort": rohantwort,
                "antwortbuchstabe": antwortbuchstabe,
                "richtige_antwort": richtige_antwort,
                "korrekt": antwortbuchstabe == richtige_antwort,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }

            ausgabe.write(json.dumps(datensatz, ensure_ascii=False) + "\n")
            ausgabe.flush()
            print(
                f"{aufrufe_gesamt}/3: {ton}, "
                f"Wiederholung {wiederholung}, Antwort {rohantwort!r}"
            )

# Kostenschätzung mit $2 pro Million Input-Tokens und
# $10 pro Million Output-Tokens.
kosten_probelauf = (
    input_tokens_gesamt * 2 / 1_000_000
    + output_tokens_gesamt * 10 / 1_000_000
)
kosten_gesamt = kosten_probelauf * anzahl_fragen_gesamt

print(f"API-Aufrufe: {aufrufe_gesamt}")
print(f"Input-Tokens: {input_tokens_gesamt}")
print(f"Output-Tokens: {output_tokens_gesamt}")
print(f"Geschätzte Kosten des Probelaufs: ${kosten_probelauf:.4f}")
print(f"Geschätzte Kosten des Gesamtlaufs: ${kosten_gesamt:.2f}")
