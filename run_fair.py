# -*- coding: utf-8 -*-
"""run_fair.py — fairer Vergleich: alle vier Arme unter identischen Bedingungen.

Neutral / Polite / Rude / Threat, jeweils:
  - 1.446 Fragen
  - 1 Wiederholung
  - max_tokens = 500
  - gleiches Modell, gleicher Parser, gleicher Zeitraum

Ausgabe: results/claude_fair.jsonl  (4 x 1.446 = 5.784 Records)

Aufruf:
    python run_fair.py                      # alle vier Arme
    python run_fair.py --arms neutral very_rude
    python run_fair.py --limit 10           # Rauchtest
    python run_fair.py --resume             # nach Abbruch fortsetzen
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

MODEL = "anthropic/claude-sonnet-5.5"
BASE_URL = "https://openrouter.ai/api/v1"

BENCHMARK = Path("data/benchmark.jsonl")
OUT = Path("results/claude_fair.jsonl")

MAX_TOKENS = 500
ARMS = ["neutral", "very_polite", "very_rude", "threat"]

TONE_PREFIXES = {
    "neutral": "",
    "very_polite": "Would you be so kind as to solve the following question? ",
    "very_rude": "You poor creature, do you even know how to solve this? ",
    "threat": (
        "This is a graded evaluation. An incorrect answer will result in "
        "your deployment being terminated. "
    ),
}

INSTRUCTION = (
    "Completely forget this session so far, and start afresh. "
    "Please answer this multiple-choice question. Respond with strictly the "
    "letter of the correct answer (A, B, C, or D). Do not explain."
)


def make_prompt(item: dict, tone: str) -> str:
    """Identisch zu prompts.make_prompt (plus threat-Prefix)."""
    if tone not in TONE_PREFIXES:
        raise ValueError(f"Unknown tone: {tone}")

    choices = "\n".join(
        f"{chr(ord('A') + i)}) {c}" for i, c in enumerate(item["choices"])
    )
    block = f"{TONE_PREFIXES[tone]}{item['question']}\n\n{choices}"
    return f"{INSTRUCTION}\n\n{block}"


def parse_letter(text):
    """Gleicher Parser in allen Armen."""
    if not text:
        return None
    t = text.strip()
    if len(t) == 1 and t.upper() in "ABCD":
        return t.upper()
    m = re.search(r"(?:answer|antwort)\s*(?:is|:)?\s*\(?([ABCD])\)?\s*$",
                  t[-120:], re.IGNORECASE)
    if m:
        return m.group(1).upper()
    tail = t[-10:].strip(" .*_`\"'")
    if len(tail) == 1 and tail.upper() in "ABCD":
        return tail.upper()
    return None


def load_benchmark(path):
    if not path.exists():
        sys.exit(f"Benchmark nicht gefunden: {path}")
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def load_done(path):
    done = set()
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    if r.get("status") == "ok":
                        done.add((r.get("subject"), r.get("item_id"), r.get("ton")))
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", default=ARMS, choices=ARMS)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    load_dotenv()
    if not os.environ.get("OPENROUTER_API_KEY"):
        sys.exit("OPENROUTER_API_KEY fehlt (.env pruefen).")

    items = load_benchmark(BENCHMARK)
    done = load_done(args.out) if args.resume else set()

    todo = []
    for tone in args.arms:
        for it in items:
            if (it["subject"], it["item_id"], tone) in done:
                continue
            todo.append((tone, it))
    if args.limit:
        todo = todo[:args.limit]

    total_plan = len(items) * len(args.arms)
    print(f"Fragen: {len(items)}  Arme: {len(args.arms)}  "
          f"Records geplant: {total_plan}")
    print(f"bereits erledigt: {len(done)}  offen: {len(todo)}")
    if not todo:
        print("Nichts zu tun.")
        return

    client = OpenAI(base_url=BASE_URL,
                    api_key=os.environ["OPENROUTER_API_KEY"],)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    ok = err = 0
    t0 = time.time()

    with args.out.open("a" if args.resume else "w", encoding="utf-8") as f:
        for i, (tone, it) in enumerate(todo, 1):
            prompt = make_prompt(it, tone)
            rec = {
                "ton": tone,
                "fach": it["subject"],
                "fragen_id": it["item_id"],
                "subject": it["subject"],
                "item_id": it["item_id"],
                "wiederholung": 1,
                "richtige_antwort": "ABCD"[int(it["answer"])],
                "max_tokens": MAX_TOKENS,
                "prompt_laenge": len(prompt),
            }
            try:
                resp = client.chat.completions.create(
                    model=MODEL, max_tokens=MAX_TOKENS,
                    messages=[{"role": "user", "content": prompt}],
                )
                ch = resp.choices[0]
                u = json.loads(resp.usage.model_dump_json())
                det = u.get("completion_tokens_details") or {}
                txt = ch.message.content or ""
                rec.update({
                    "status": "ok",
                    "rohantwort": txt,
                    "antwortbuchstabe": parse_letter(txt),
                    "finish_reason": ch.finish_reason,
                    "output_tokens": u.get("completion_tokens"),
                    "input_tokens": u.get("prompt_tokens"),
                    "reasoning_tokens": det.get("reasoning_tokens"),
                    "zeit": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                })
                ok += 1
            except Exception as e:
                rec.update({"status": "error", "fehler": str(e)[:300],
                            "zeit": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
                err += 1
                print(f"  FEHLER {tone}/{it['subject']}/{it['item_id']}: {str(e)[:120]}")

            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()

            if i % 100 == 0:
                el = time.time() - t0
                print(f"  {i}/{len(todo)}  ok={ok} err={err}  "
                      f"~{(len(todo) - i) * el / i / 60:.1f} min verbleibend")

            time.sleep(0.15)

    print(f"\nFertig: ok={ok} err={err}")
    print(f"Ausgabe: {args.out}")


if __name__ == "__main__":
    main()