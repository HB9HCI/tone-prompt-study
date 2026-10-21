import argparse
import json
import os
from pathlib import Path

from openai import OpenAI

from prompts import TONE_PREFIXES, make_prompt
from answer_utils import parse_answer
import re

BENCHMARK_PATH = Path("data/benchmark.jsonl")
OUTPUT_PATH = Path("results/claude_full.jsonl") 
MODEL = "anthropic/claude-sonnet-5.5"
EXPECTED_QUESTIONS = 1446
REPETITIONS = 10


def load_questions(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def answer_letter(answer_index: int) -> str:
    """Wandelt den Benchmark-Antwortindex 0–3 in A–D um."""
    if answer_index not in range(4):
        raise ValueError(f"Ungültiger Antwortindex: {answer_index}")
    return "ABCD"[answer_index]


def task_key(record: dict) -> tuple:
    """Eindeutiger Schlüssel für Frage, Ton und Wiederholung."""
    return (
        record["fach"],
        record["fragen_id"],
        record["ton"],
        record["wiederholung"],
    )


def load_successful_tasks(path: Path) -> set[tuple]:
    """Überspringt nur erfolgreich gespeicherte Antworten im Format A–D."""
    completed = set()
    if not path.exists():
        return completed

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            record = json.loads(line)
            raw_answer = record.get("rohantwort")

            if (
                record.get("status") == "ok"
                and isinstance(raw_answer, str)
                and re.fullmatch(r"[A-D]", raw_answer.strip())
            ):
                completed.add(task_key(record))

    return completed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execute",
        action="store_true",
        help="API-Aufrufe tatsächlich ausführen. Ohne diese Option nur lokal prüfen.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Vorhandene Ergebnisdatei fortsetzen; erfolgreiche Aufgaben überspringen.",
    )
    args = parser.parse_args()

    if args.resume and not OUTPUT_PATH.exists():
        parser.error(f"Keine vorhandene Ergebnisdatei zum Fortsetzen: {OUTPUT_PATH}")

    questions = load_questions(BENCHMARK_PATH)
    questions = questions[:EXPECTED_QUESTIONS]  # Nur die erwartete Anzahl an Fragen verwenden
    if len(questions) != EXPECTED_QUESTIONS:
        raise ValueError(
            f"Erwartet wurden {EXPECTED_QUESTIONS} Fragen, "
            f"gefunden wurden {len(questions)}."
        )

    tones = list(TONE_PREFIXES.keys())
    planned_calls = len(questions) * len(tones) * REPETITIONS

    print(f"Fragen: {len(questions)}")
    print(f"Tonbedingungen: {', '.join(tones)}")
    print(f"Wiederholungen je Frage und Ton: {REPETITIONS}")
    print(f"Geplante API-Aufrufe: {planned_calls}")
    print(f"Ausgabedatei: {OUTPUT_PATH}")

    if not args.execute:
        print("Lokaler Prüflauf abgeschlossen; es wurden keine API-Aufrufe ausgeführt.")
        print("Für den tatsächlichen Lauf wäre zusätzlich --execute erforderlich.")
        return

    # Schlüssel bleibt lokal in der Umgebung/.env; er wird nicht ausgegeben.
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY ist in der Umgebung nicht gesetzt.")

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT_PATH.exists() and not args.resume:
        raise FileExistsError(
            f"{OUTPUT_PATH} existiert bereits. "
            "Nutze --resume zum Fortsetzen oder wähle bewusst einen neuen Dateinamen."
        )

    completed = load_successful_tasks(OUTPUT_PATH) if args.resume else set()
    output_mode = "a" if args.resume else "x"

    calls_done = 0
    with OUTPUT_PATH.open(output_mode, encoding="utf-8") as output:
        for question in questions:
            correct_letter = answer_letter(question["answer"])

            for tone in tones:
                for repetition in range(1, REPETITIONS + 1):
                    planned_record = {
                        "fach": question["subject"],
                        "fragen_id": question["item_id"],
                        "ton": tone,
                        "wiederholung": repetition,
                    }

                    if task_key(planned_record) in completed:
                        continue

                    try:
                        response = client.chat.completions.create(
                            model=MODEL,
                            messages=[
                                {
                                    "role": "user",
                                    "content": make_prompt(question, tone),
                                }
                            ],
                            max_tokens=100,
                        )
                    except Exception as error:
                        # Kein automatischer Retry. Bereits geschriebene
                        # Ergebnisse bleiben erhalten; der Lauf stoppt.
                        failure_record = {
                            **planned_record,
                            "modell": MODEL,
                            "status": "error",
                            "fehler": str(error),
                        }
                        output.write(
                            json.dumps(failure_record, ensure_ascii=False) + "\n"
                        )
                        output.flush()
                        raise RuntimeError(
                            "API-Aufruf fehlgeschlagen; Lauf wurde gestoppt. "
                            "Gespeicherte Ergebnisse bleiben in der JSONL-Datei."
                        ) from error

                    raw_answer = response.choices[0].message.content or ""
                    parsed_answer = parse_answer(raw_answer)
                    usage = response.usage

                    record = {
                        **planned_record,
                        "modell": response.model,
                        "status": "ok",
                        "rohantwort": raw_answer,
                        "antwortbuchstabe": parsed_answer,
                        "richtige_antwort": correct_letter,
                        "korrekt": parsed_answer == correct_letter,
                        "input_tokens": usage.prompt_tokens if usage else 0,
                        "output_tokens": usage.completion_tokens if usage else 0,
                        "finish_reason": response.choices[0].finish_reason,
                    }

                    output.write(json.dumps(record, ensure_ascii=False) + "\n")
                    output.flush()
                    calls_done += 1

                    print(
                        f"{calls_done}/{planned_calls} Aufrufe in diesem Lauf abgeschlossen ",
                        f"{tone}, Wiederholung {repetition}",
                        flush=True,
                    )


if __name__ == "__main__":
    main()
