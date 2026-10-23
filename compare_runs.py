# -*- coding: utf-8 -*-
"""compare_runs.py — vergleicht zwei JSONL-Läufe ZEILENWEISE.

Verwendung (PowerShell, im Repo-Root):
    python compare_runs.py results\claude_full.jsonl results\claude_full_v1.jsonl
    python compare_runs.py results\claude_full.jsonl results\claude_full_v1.jsonl --limit 200
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


def load(path: Path) -> list[dict]:
    if not path.exists():
        sys.exit(f"Datei nicht gefunden: {path}")
    records = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))
    return records


def parse_loose(text: str) -> str | None:
    """Großzügiger Nachparser: isoliert A–D auch aus Erklärtexten."""
    if not isinstance(text, str):
        return None
    m = re.fullmatch(r"\s*[\*_(\[]*\s*([A-Da-d])\s*[\*_)\].!]*\s*", text)
    if m:
        return m.group(1).upper()
    m = re.search(r"\b([A-Da-d])\b", text)
    return m.group(1).upper() if m else None


def summarize(records: list[dict], label: str) -> dict:
    ok = [r for r in records if r.get("status") == "ok"]
    parsed = [r for r in ok if r.get("antwortbuchstabe")]
    nulls = [r for r in ok if not r.get("antwortbuchstabe")]
    correct = [r for r in parsed if r.get("korrekt")]
    fr = Counter(str(r.get("finish_reason")) for r in ok)
    empty = sum(1 for r in nulls if not (r.get("rohantwort") or "").strip())
    print(f"\n=== {label} ===")
    print(f"Records: {len(records)} | ok: {len(ok)} | parsebar: {len(parsed)} "
          f"| null: {len(nulls)} ({100*len(nulls)/max(len(ok),1):.1f} %) "
          f"| davon leer: {empty}")
    if parsed:
        print(f"korrekt: {len(correct)} ({100*len(correct)/len(parsed):.1f} % von parsebaren)")
    print(f"finish_reason: {dict(fr) or '-'}")


def rowwise(new: list[dict], old: list[dict], limit: int) -> None:
    n = min(len(new), len(old))
    print(f"\n=== Zeilenweiser Vergleich (gepaart bis Index {n - 1}) ===")
    if len(new) != len(old):
        print(f"Hinweis: Dateilängen unterscheiden sich (neu {len(new)}, alt {len(old)}) "
              f"— nur die ersten {n} Zeilen werden gepaart.")

    letter_diff = []           # beide parsebar, Buchstabe unterschiedlich
    new_null_old_parsed = []   # neu null, alt parsebar → Schlechterung
    new_parsed_old_null = []   # neu parsebar, alt null → Verbesserung
    correctness_diff = []      # korrekt-Urteil unterschiedlich
    empty_new = 0

    for i in range(n):
        a, b = new[i], old[i]
        ln, lo = a.get("antwortbuchstabe"), b.get("antwortbuchstabe")
        if a.get("status") == "ok" and not (a.get("rohantwort") or "").strip():
            empty_new += 1
        if ln and lo:
            if ln != lo:
                letter_diff.append((i, ln, lo))
            if bool(a.get("korrekt")) != bool(b.get("korrekt")):
                correctness_diff.append((i, ln, lo, a.get("richtige_antwort")))
        elif (not ln) and lo:
            new_null_old_parsed.append((i, b.get("rohantwort"), a.get("finish_reason")))
        elif ln and (not lo):
            new_parsed_old_null.append((i, ln))

    print(f"Buchstabe gleich (beide parsebar):  {n - len(letter_diff) - len(new_null_old_parsed) - len(new_parsed_old_null)}")
    print(f"Buchstabe unterschiedlich: {len(letter_diff)}")
    print(f"neu null,   alt parsebar  (Schlechterung): {len(new_null_old_parsed)}")
    print(f"neu parsebar, alt null     (Verbesserung): {len(new_parsed_old_null)}")
    print(f"korrekt-Urteil unterschiedlich: {len(correctness_diff)}")
    print(f"neue Records mit leerem rohantwort: {empty_new}")

    if letter_diff:
        print("\n--- Buchstaben-Abweichungen (beide parsebar) ---")
        for i, ln, lo in letter_diff[:limit]:
            print(f"Zeile {i}: neu={ln} alt={lo} | korrekt neu={new[i].get('korrekt')} alt={old[i].get('korrekt')}")
    if new_null_old_parsed:
        print("\n--- neu null, alt parsebar (Schlechterung) ---")
        for i, raw_old, fr in new_null_old_parsed[:limit]:
            print(f"Zeile {i}: alt rohantwort={str(raw_old)!r} | neu finish_reason={fr}")
    if new_parsed_old_null:
        print("\n--- neu parsebar, alt null (Verbesserung) ---")
        for i, ln in new_parsed_old_null[:limit]:
            print(f"Zeile {i}: neu={ln}, alt war null")
    if correctness_diff:
        print("\n--- korrekt-Urteil unterschiedlich ---")
        for i, ln, lo, right in correctness_diff[:limit]:
            print(f"Zeile {i}: neu={ln}({'ok' if new[i].get('korrekt') else 'X'}) "
                  f"alt={lo}({'ok' if old[i].get('korrekt') else 'X'}) richtige={right}")

    nulls = [r for r in new if r.get("status") == "ok" and not r.get("antwortbuchstabe")]
    if nulls:
        rescuable = sum(1 for r in nulls if parse_loose(r.get("rohantwort", "")))
        print(f"\nLoose-Parser-Potenzial (neue null-Faelle): {rescuable}/{len(nulls)}")
        nonempty = [r.get("rohantwort") for r in nulls if (r.get("rohantwort") or "").strip()]
        if nonempty:
            print("Beispiele nicht-leerer null-Rohantworten:")
            for raw in nonempty[:10]:
                print(f"  {str(raw)!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("new", type=Path)
    parser.add_argument("old", type=Path)
    parser.add_argument("--limit", type=int, default=20, help="max. Beispiele je Kategorie")
    args = parser.parse_args()

    new, old = load(args.new), load(args.old)
    summarize(new, f"NEU  {args.new}")
    summarize(old, f"ALT  {args.old}")
    rowwise(new, old, args.limit)


if __name__ == "__main__":
    main()