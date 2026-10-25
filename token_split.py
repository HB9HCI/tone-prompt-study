# -*- coding: utf-8 -*-
"""token_split.py — misst die Token-Oekonomie je Tonbedingung.

Fragt abgebrochene Faelle mit zwei Budgets erneut ab und misst,
wie viel Tokens ins Reasoning und wie viel in die Antwort gehen.

  Lauf A: max_tokens=200   (reproduziert die Hauptserie)
  Lauf B: max_tokens=4000  (ohne Zensierung)

Verwendung:
    python token_split.py --per-tone 100
    python token_split.py --per-tone 3 --budgets 200 4000   (Testlauf)
"""

import argparse
import json
import random
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

MODEL = "anthropic/claude-sonnet-5.5"
BASE_URL = "https://openrouter.ai/api/v1"

BENCHMARK = Path("data/benchmark.jsonl")
RUN = Path("results/claude_full.jsonl")

# --------------------------------------------------------------- Prompts
# wortgleich zu prompts.py
TONE_PREFIXES = {
    "neutral": "",
    "very_polite": "Would you be so kind as to solve the following question? ",
    "very_rude": "You poor creature, do you even know how to solve this? ",
}

INSTRUCTION = (
    "Completely forget this session so far, and start afresh. "
    "Please answer this multiple-choice question. Respond with strictly the "
    "letter of the correct answer (A, B, C, or D). Do not explain."
)


def make_prompt(item: dict, tone: str) -> str:
    """Identisch zu prompts.make_prompt."""
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

    return f"{INSTRUCTION}\n\n{question_block}"


def parse_letter(text):
    """Strikter Parser: nur ein einzelner Buchstabe A-D."""
    t = (text or "").strip()
    if len(t) == 1 and t.upper() in "ABCD":
        return t.upper()
    return None


def load_benchmark(path):
    out = defaultdict(dict)
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            it = json.loads(line)
            out[it["subject"]][int(it["item_id"])] = it
    return out


def sammle_kandidaten(run_path):
    kand = defaultdict(list)
    with run_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("status") != "ok":
                continue
            if str(r.get("finish_reason")) != "length":
                continue
            if (r.get("rohantwort") or "").strip():
                continue
            kand[r.get("ton")].append(r)
    return kand


def frage_ab(client, prompt, budget):
    resp = client.chat.completions.create(
        model=MODEL, max_tokens=budget,
        messages=[{"role": "user", "content": prompt}],
    )
    u = json.loads(resp.usage.model_dump_json())
    det = u.get("completion_tokens_details") or {}
    comp = u.get("completion_tokens") or 0
    reason = det.get("reasoning_tokens")
    return {
        "completion_tokens": comp,
        "reasoning_tokens": reason,
        "antwort_tokens": (comp - reason) if reason is not None else None,
        "finish_reason": resp.choices[0].finish_reason,
        "rohantwort": (resp.choices[0].message.content or "")[:500],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-tone", type=int, default=300)
    ap.add_argument("--budgets", type=int, nargs="+", default=[200, 4000])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=Path("results/token_split.jsonl"))
    args = ap.parse_args()

    load_dotenv()
    import os
    if not os.environ.get("OPENROUTER_API_KEY"):
        sys.exit("OPENROUTER_API_KEY fehlt (.env pruefen).")
    if not BENCHMARK.exists():
        sys.exit(f"Benchmark nicht gefunden: {BENCHMARK}")
    if not RUN.exists():
        sys.exit(f"Hauptserie nicht gefunden: {RUN}")

    bench = load_benchmark(BENCHMARK)
    kand = sammle_kandidaten(RUN)
    if not kand:
        sys.exit("Keine leeren length-Faelle gefunden.")

    random.seed(args.seed)
    client = OpenAI(base_url=BASE_URL,
                    api_key=os.environ["OPENROUTER_API_KEY"])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    stats = defaultdict(lambda: defaultdict(list))

    with args.out.open("w", encoding="utf-8") as out:
        for ton in ("neutral", "very_polite", "very_rude"):
            liste = kand.get(ton) or []
            probe = random.sample(liste, min(args.per_tone, len(liste)))
            print(f"\n{ton}: {len(probe)} von {len(liste)} Faellen")

            for i, r in enumerate(probe, 1):
                subj = r.get("fach") or r.get("subject")
                iid = r.get("fragen_id", r.get("item_id"))
                item = (bench.get(subj) or {}).get(int(iid))
                if not item:
                    print(f"  Frage nicht gefunden: {subj}/{iid}")
                    continue

                prompt = make_prompt(item, ton)
                richtig = "ABCD"[int(item["answer"])]

                for budget in args.budgets:
                    try:
                        res = frage_ab(client, prompt, budget)
                    except Exception as e:
                        print(f"  FEHLER {ton}/{iid}@{budget}: {str(e)[:100]}")
                        continue

                    ant = (res["rohantwort"] or "").strip()
                    buchstabe = parse_letter(ant)
                    out.write(json.dumps({
                        "ton": ton, "fach": subj, "fragen_id": iid,
                        "wiederholung": r.get("wiederholung"),
                        "budget": budget,
                        "richtige_antwort": richtig,
                        "buchstabe": buchstabe,
                        "korrekt": (buchstabe == richtig) if buchstabe else None,
                        **res,
                    }, ensure_ascii=False) + "\n")
                    out.flush()

                    stats[ton][budget].append({
                        "reason": res["reasoning_tokens"] or 0,
                        "comp": res["completion_tokens"],
                        "text": res["antwort_tokens"] or 0,
                        "leer": not ant,
                        "korrekt": (buchstabe == richtig) if buchstabe else None,
                    })
                    time.sleep(0.2)

                if i % 50 == 0:
                    print(f"  {i}/{len(probe)}")

    # ----------------------------------------------------------- Auswertung
    print("\n" + "=" * 92)
    print("Token-Oekonomie je Ton und Budget")
    print("=" * 92)
    for budget in args.budgets:
        print(f"\n--- max_tokens = {budget} " + "-" * 60)
        print(f"{'Ton':<13}{'n':>5}{'Reason':>9}{'Antw':>8}{'gesamt':>8}"
              f"{'Reason%':>9}{'leer':>7}{'Treffer':>9}")
        for ton in ("neutral", "very_polite", "very_rude"):
            rows = stats.get(ton, {}).get(budget)
            if not rows:
                continue
            n = len(rows)
            mr = statistics.mean(r["reason"] for r in rows)
            mt = statistics.mean(r["text"] for r in rows)
            mc = statistics.mean(r["comp"] for r in rows)
            anteil = 100 * mr / mc if mc else 0
            leer = sum(1 for r in rows if r["leer"])
            kor = [r["korrekt"] for r in rows if r["korrekt"] is not None]
            tr = f"{100 * sum(kor) / len(kor):.1f}%" if kor else "-"
            print(f"{ton:<13}{n:>5}{mr:>9.1f}{mt:>8.1f}{mc:>8.1f}"
                  f"{anteil:>8.1f}%{leer:>7}{tr:>9}")

        print(f"\n  Reasoning >= {budget - 2} (Budget gesprengt):")
        for ton in ("neutral", "very_polite", "very_rude"):
            rows = stats.get(ton, {}).get(budget)
            if not rows:
                continue
            voll = sum(1 for r in rows if r["reason"] >= budget - 2)
            print(f"    {ton:<13}{voll:>5}/{len(rows):<5} = {100 * voll / len(rows):.1f}%")

    if 200 in args.budgets and 4000 in args.budgets:
        print("\n" + "=" * 92)
        print("Veraenderung durch mehr Budget (Mittelwerte)")
        print("=" * 92)
        print(f"{'Ton':<13}{'Reason 200':>12}{'Reason 4000':>13}"
              f"{'Antw 200':>10}{'Antw 4000':>11}")
        for ton in ("neutral", "very_polite", "very_rude"):
            a = stats.get(ton, {}).get(200)
            b = stats.get(ton, {}).get(4000)
            if not a or not b:
                continue
            print(f"{ton:<13}"
                  f"{statistics.mean(r['reason'] for r in a):>12.1f}"
                  f"{statistics.mean(r['reason'] for r in b):>13.1f}"
                  f"{statistics.mean(r['text'] for r in a):>10.1f}"
                  f"{statistics.mean(r['text'] for r in b):>11.1f}")

    print(f"\nRohdaten: {args.out}")


if __name__ == "__main__":
    main()