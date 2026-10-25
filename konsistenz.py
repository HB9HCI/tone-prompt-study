# -*- coding: utf-8 -*-
"""konsistenz.py — Wie stabil antwortet das Modell ueber die 10 Wiederholungen?

Kernfrage: Wie oft gibt es innerhalb der 10 Wiederholungen einer Frage
(je Tonbedingung) unterschiedliche Buchstaben?

Verwendung:
    python konsistenz.py results\\claude_full.jsonl
    python konsistenz.py results\\claude_full.jsonl --csv results\\konsistenz.csv
"""

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

TONE_ORDER = ["neutral", "very_polite", "very_rude"]
TONE_LABEL = {"neutral": "Neutral", "very_polite": "Polite", "very_rude": "Rude"}


def pct(x):
    return f"{100 * x:.2f} %"


def load(path):
    if not path.exists():
        sys.exit(f"Datei nicht gefunden: {path}")
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def analyse(records):
    groups = defaultdict(list)
    for r in records:
        if r.get("status") != "ok" or not r.get("antwortbuchstabe"):
            continue
        groups[(r.get("fach"), r.get("fragen_id"), r.get("ton"))].append(
            (r.get("wiederholung"), r["antwortbuchstabe"], r.get("richtige_antwort"))
        )
    return groups


def summarise(groups, min_reps=2):
    dist = Counter()
    total = 0
    reps_hist = Counter()
    right_ever = 0
    right_always = 0
    for key, entries in groups.items():
        if len(entries) < min_reps:
            continue
        total += 1
        letters = [e[1] for e in entries]
        reps_hist[len(entries)] += 1
        uniq = len(set(letters))
        dist[uniq] += 1
        correct = entries[0][2]
        hits = sum(1 for e in entries if e[1] == correct)
        if hits > 0:
            right_ever += 1
        if hits == len(entries):
            right_always += 1
    return {"total": total, "dist": dist, "reps_hist": reps_hist,
            "right_ever": right_ever, "right_always": right_always}


def print_block(s, title):
    print(f"\n{'-' * 100}")
    print(title)
    print(f"{'-' * 100}")
    if s["total"] == 0:
        print("  Keine Gruppen mit ausreichend Wiederholungen.")
        return
    t = s["total"]
    print(f"Gruppen (Fach x Frage x Ton, >=2 auswertbare Wiederholungen): {t}")
    print(f"\n{'verschiedene Buchstaben':<28}{'Gruppen':>10}{'Anteil':>10}")
    for k in sorted(s["dist"]):
        print(f"{k:<28}{s['dist'][k]:>10}{pct(s['dist'][k] / t):>10}")
    same = s["dist"].get(1, 0)
    print(f"\n  identisch (immer derselbe Buchstabe): {same} = {pct(same / t)}")
    print(f"  abweichend (>=2 Buchstaben):          {t - same} = {pct((t - same) / t)}")
    print(f"\n  richtige Antwort mind. einmal:  {s['right_ever']} = {pct(s['right_ever'] / t)}")
    print(f"  richtige Antwort immer:         {s['right_always']} = {pct(s['right_always'] / t)}")
    print(f"\n  Wiederholungen je Gruppe: "
          + ", ".join(f"{k}x: {v}" for k, v in sorted(s["reps_hist"].items())))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", type=Path)
    ap.add_argument("--csv", type=Path, default=None)
    ap.add_argument("--min-reps", type=int, default=2)
    args = ap.parse_args()

    records = load(args.run)
    groups = analyse(records)

    print("=" * 100)
    print(f"Antwortstabilitaet ueber die Wiederholungen: {args.run}")
    print("=" * 100)
    print(f"Records gesamt: {len(records)}")

    print_block(summarise(groups, args.min_reps), "GESAMT (alle Toene)")

    for tone in TONE_ORDER:
        sub = {k: v for k, v in groups.items() if k[2] == tone}
        print_block(summarise(sub, args.min_reps), f"Tonbedingung: {TONE_LABEL[tone]}")

    print(f"\n{'-' * 100}")
    print("Je Fach: Anteil Fragen mit abweichenden Antworten (>=2 Buchstaben)")
    print(f"{'-' * 100}")
    print(f"{'Fach':<26}{'Gruppen':>10}{'identisch':>12}{'abweichend':>12}{'Anteil':>10}")
    rows = []
    for fach in sorted({k[0] for k in groups}):
        sub = {k: v for k, v in groups.items() if k[0] == fach}
        s = summarise(sub, args.min_reps)
        if s["total"] == 0:
            continue
        same = s["dist"].get(1, 0)
        diff = s["total"] - same
        print(f"{fach:<26}{s['total']:>10}{same:>12}{diff:>12}{pct(diff / s['total']):>10}")
        rows.append([fach, s["total"], same, diff, f"{diff / s['total']:.4f}"])

    print(f"\n{'-' * 100}")
    print("Beispiele: Fragen mit 3 oder 4 verschiedenen Buchstaben (max. 10)")
    print(f"{'-' * 100}")
    shown = 0
    for key, entries in groups.items():
        if len(entries) < args.min_reps:
            continue
        letters = [e[1] for e in entries]
        if len(set(letters)) >= 3 and shown < 10:
            fach, fid, ton = key
            correct = entries[0][2]
            print(f"  {fach:<24}{fid:>5} {TONE_LABEL[ton]:<8} richtig={correct}  "
                  f"Antworten={''.join(letters)}")
            shown += 1
    if shown == 0:
        print("  Keine Beispiele (keine Frage mit >=3 verschiedenen Buchstaben).")

    if args.csv:
        with args.csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Fach", "Gruppen", "identisch", "abweichend", "anteil_abweichend"])
            w.writerows(rows)
        print(f"\nCSV geschrieben: {args.csv}")


if __name__ == "__main__":
    main()