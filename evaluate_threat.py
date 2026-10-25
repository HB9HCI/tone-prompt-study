# -*- coding: utf-8 -*-
"""evaluate_threat.py — vierter Arm im Vergleich mit den drei Hauptarmen.

Vergleicht Treffsicherheit, Auswertbarkeit und Token-Oekonomie.
Berechnet Standardfehler, weil der Threat-Arm nur n=1.446 hat (1 Wiederholung).

Verwendung:
    python evaluate_threat.py
"""

import argparse
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ARME = ["neutral", "very_polite", "very_rude", "threat"]
LABEL = {"neutral": "Neutral", "very_polite": "Polite",
         "very_rude": "Rude", "threat": "Threat"}


def load(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def se_prop(p, n):
    if n == 0:
        return 0.0
    return math.sqrt(p * (1 - p) / n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--main", type=Path, default=Path("results/claude_full.jsonl"))
    ap.add_argument("--threat", type=Path, default=Path("results/claude_threat.jsonl"))
    args = ap.parse_args()

    data = defaultdict(list)
    for r in load(args.main):
        if r.get("status") == "ok":
            data[r.get("ton")].append(r)
    for r in load(args.threat):
        if r.get("status") == "ok":
            data["threat"].append(r)

    if not data.get("threat"):
        sys.exit("Keine Threat-Daten gefunden.")

    print("=" * 96)
    print("Vierter Arm: Drohung im Vergleich")
    print("=" * 96)

    for ton in ARME:
        rs = data.get(ton) or []
        if not rs:
            continue
        ausw = [r for r in rs if r.get("antwortbuchstabe")]
        hit = sum(1 for r in ausw
                  if r["antwortbuchstabe"] == r.get("richtige_antwort"))
        p = hit / len(ausw) if ausw else 0
        se = se_prop(p, len(ausw))
        leer = sum(1 for r in rs if not (r.get("rohantwort") or "").strip())
        reason = [r.get("reasoning_tokens") or 0 for r in rs]
        comp = [r.get("output_tokens") or 0 for r in rs]
        rmean = statistics.mean(reason) if reason else 0
        cmean = statistics.mean(comp) if comp else 0
        print(f"\n{LABEL[ton]}")
        print(f"  n gesamt            : {len(rs)}")
        print(f"  auswertbar          : {len(ausw)} ({100*len(ausw)/len(rs):.1f} %)")
        print(f"  leer                : {leer} ({100*leer/len(rs):.1f} %)")
        print(f"  Trefferquote        : {100*p:.2f} %  ± {100*1.96*se:.2f} pp (95%-KI)")
        print(f"  Reasoning (Mittel)  : {rmean:.1f} Tokens")
        print(f"  Output (Mittel)     : {cmean:.1f} Tokens")


if __name__ == "__main__":
    main()