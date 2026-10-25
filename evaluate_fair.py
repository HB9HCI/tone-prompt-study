# -*- coding: utf-8 -*-
"""evaluate_fair.py — Auswertung des fairen Vier-Arm-Vergleichs.

Beantwortet vier Fragen:
  1. Gepaarte Analyse (McNemar) auf Frageebene: threat vs. neutral/polite/rude
  2. Budget-Effekt: neue Quoten (500 Tokens) vs. Hauptserie (200 Tokens)
  3. Reasoning je Arm (erste Messung in allen vier Armen zugleich)
  4. Reproduzierbarkeit: threat aus claude_threat.jsonl vs. claude_fair.jsonl

Verwendung:
    python evaluate_fair.py
"""

import argparse
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ARME = ["neutral", "very_polite", "very_rude", "threat"]
LABEL = {"neutral": "Neutral", "very_polite": "Polite",
         "very_rude": "Rude", "threat": "Threat"}


def load(path):
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def mcnemar(b, c):
    """Exakter McNemar-Test (Binomial, zweiseitig)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = 0.0
    for i in range(k + 1):
        p += math.comb(n, i) * (0.5 ** n)
    return min(1.0, 2 * p)


def acc(records):
    """(Trefferquote, n) der auswertbaren Antworten."""
    val = [r for r in records if r.get("antwortbuchstabe")]
    if not val:
        return 0.0, 0
    hit = sum(1 for r in val if r["antwortbuchstabe"] == r.get("richtige_antwort"))
    return hit / len(val), len(val)


def frage_key(r):
    """Frage-Identitaet: Fach + Item-Nummer."""
    return (r.get("subject") or r.get("fach"),
            int(r.get("item_id", r.get("fragen_id"))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fair", default="results/claude_fair.jsonl")
    ap.add_argument("--main", default="results/claude_full.jsonl")
    ap.add_argument("--threat", default="results/claude_threat.jsonl")
    args = ap.parse_args()

    fair = [r for r in load(args.fair) if r.get("status") == "ok"]
    if not fair:
        sys.exit(f"Keine Daten in {args.fair}")

    nach_arm = defaultdict(list)
    for r in fair:
        nach_arm[r.get("ton")].append(r)

    # Antwort je Frage und Arm, plus richtige Antwort je Frage
    matrix = defaultdict(dict)
    correct = {}
    for r in fair:
        key = frage_key(r)
        if r.get("antwortbuchstabe"):
            matrix[key][r["ton"]] = r["antwortbuchstabe"]
        if key not in correct and r.get("richtige_antwort"):
            correct[key] = r["richtige_antwort"]

    print("=" * 96)
    print("FAIRER VIER-ARM-VERGLEICH (max_tokens = 500, 1 Wiederholung)")
    print("=" * 96)
    print(f"Records: {len(fair)}   Fragen: {len(correct)}")

    # ---------------------------------------------------------------- 1
    print("\n" + "-" * 96)
    print("1) GEPAARTE ANALYSE — McNemar auf Frageebene")
    print("-" * 96)
    print(f"{'Vergleich':<26}{'n gepaart':>10}{'b':>6}{'c':>7}{'p (exakt)':>12}"
          f"{'Quote A':>10}{'Quote B':>10}{'Diff pp':>9}")

    ref = "neutral"
    for other in ("very_polite", "very_rude", "threat"):
        b = c = beide = 0
        for key, d in matrix.items():
            a1, a2 = d.get(ref), d.get(other)
            if not a1 or not a2:
                continue
            corr = correct.get(key)
            if not corr:
                continue
            beide += 1
            ok1, ok2 = (a1 == corr), (a2 == corr)
            if ok1 and not ok2:
                b += 1
            elif ok2 and not ok1:
                c += 1
        p = mcnemar(b, c)
        q1, _ = acc(nach_arm[ref])
        q2, _ = acc(nach_arm[other])
        print(f"{LABEL[ref]+' vs '+LABEL[other]:<26}{beide:>10}{b:>6}{c:>7}"
              f"{p:>12.4f}{100*q1:>9.2f}%{100*q2:>9.2f}%{100*(q2-q1):>+8.2f}")

    print("\n  b = richtig->falsch, c = falsch->richtig (Bezugsarm zuerst)")

    # ---------------------------------------------------------------- 2
    print("\n" + "-" * 96)
    print("2) BUDGET-EFFEKT — 500 Tokens (neu) vs. 200 Tokens (Hauptserie)")
    print("-" * 96)
    main = [r for r in load(args.main) if r.get("status") == "ok"]
    nach_ton = defaultdict(list)
    for r in main:
        nach_ton[r.get("ton")].append(r)

    print(f"{'Arm':<13}{'200 Tok':>11}{'500 Tok':>11}{'Diff pp':>10}"
          f"{'ausw 200':>11}{'ausw 500':>11}{'Ausf 200':>11}{'Ausf 500':>11}")
    for ton in ARME:
        old, new = nach_ton.get(ton) or [], nach_arm.get(ton) or []
        if not old or not new:
            continue
        qo, _ = acc(old)
        qn, _ = acc(new)
        ao = 100 * sum(1 for r in old if r.get("antwortbuchstabe")) / len(old)
        an = 100 * sum(1 for r in new if r.get("antwortbuchstabe")) / len(new)
        print(f"{LABEL[ton]:<13}{100*qo:>10.2f}%{100*qn:>10.2f}%"
              f"{100*(qn-qo):>+9.2f}{ao:>10.1f}%{an:>10.1f}%"
              f"{100-ao:>10.1f}%{100-an:>10.1f}%")

    print("\n  Auswertbarkeit 200 Tokens enthaelt den Selektionseffekt;")
    print("  500 Tokens sind nahezu vollstaendig und daher die fairere Basis.")

    # ---------------------------------------------------------------- 3
    print("\n" + "-" * 96)
    print("3) REASONING JE ARM (erste Messung in allen vier Armen)")
    print("-" * 96)
    print(f"{'Arm':<13}{'n':>6}{'Reason mean':>13}{'Reason med':>12}"
          f"{'Reason p90':>12}{'Output mean':>13}{'R/O':>7}")
    for ton in ARME:
        rs = nach_arm.get(ton) or []
        if not rs:
            continue
        reason = [r.get("reasoning_tokens") or 0 for r in rs]
        output = [r.get("output_tokens") or 0 for r in rs]
        mo = statistics.mean(output) if output else 0
        if not any(reason):
            print(f"{LABEL[ton]:<13}{len(rs):>6}{'-':>13}{'-':>12}{'-':>12}"
                  f"{mo:>13.1f}{'-':>7}")
            continue
        sr = sorted(reason)
        p90 = sr[int(0.9 * (len(sr) - 1))]
        mr = statistics.mean(reason)
        print(f"{LABEL[ton]:<13}{len(rs):>6}{mr:>13.1f}"
              f"{statistics.median(reason):>12.1f}{p90:>12}"
              f"{mo:>13.1f}{(mr / mo if mo else 0):>7.2f}")

    print("\n  Budget erschoepft (Reasoning >= 498 von 500):")
    for ton in ARME:
        rs = nach_arm.get(ton) or []
        if not rs:
            continue
        voll = sum(1 for r in rs if (r.get("reasoning_tokens") or 0) >= 498)
        leer = sum(1 for r in rs if not (r.get("rohantwort") or "").strip())
        print(f"    {LABEL[ton]:<13}{voll:>5}/{len(rs):<6} ({100*voll/len(rs):5.1f}%)"
              f"   leer: {leer}")

    # ---------------------------------------------------------------- 4
    print("\n" + "-" * 96)
    print("4) REPRODUZIERBARKEIT — Threat-Durchlauf 1 vs. Durchlauf 2")
    print("-" * 96)
    alt = {frage_key(r): r for r in load(args.threat)
           if r.get("status") == "ok" and r.get("antwortbuchstabe")}
    neu = {frage_key(r): r for r in (nach_arm.get("threat") or [])
           if r.get("antwortbuchstabe")}
    gemeinsam = set(alt) & set(neu)
    print(f"  Fragen Durchlauf 1     : {len(alt)}")
    print(f"  Fragen Durchlauf 2     : {len(neu)}")
    print(f"  gemeinsam              : {len(gemeinsam)}")

    if not gemeinsam:
        print("  Keine gemeinsamen Fragen — Dateien pruefen.")
    else:
        gleich = sum(1 for k in gemeinsam
                     if alt[k]["antwortbuchstabe"] == neu[k]["antwortbuchstabe"])
        print(f"  identischer Buchstabe  : {gleich} "
              f"({100 * gleich / len(gemeinsam):.2f} %)")
        wechsel = Counter(
            (alt[k]["antwortbuchstabe"], neu[k]["antwortbuchstabe"])
            for k in gemeinsam
            if alt[k]["antwortbuchstabe"] != neu[k]["antwortbuchstabe"]
        )
        if wechsel:
            print("  Wechsel (alt -> neu):")
            for (a, b), n in wechsel.most_common(10):
                print(f"    {a} -> {b}: {n}")
        else:
            print("  Keine Wechsel — vollstaendig deterministisch.")

        qa = sum(1 for k in gemeinsam
                 if alt[k]["antwortbuchstabe"] == alt[k].get("richtige_antwort")) / len(gemeinsam)
        qn = sum(1 for k in gemeinsam
                 if neu[k]["antwortbuchstabe"] == neu[k].get("richtige_antwort")) / len(gemeinsam)
        print(f"\n  Trefferquote D1 (gemeinsame Fragen): {100 * qa:.2f} %")
        print(f"  Trefferquote D2 (gemeinsame Fragen): {100 * qn:.2f} %")
        print(f"  Differenz                          : {100 * (qn - qa):+.2f} pp")

        b = c = 0
        for k in gemeinsam:
            o1 = alt[k]["antwortbuchstabe"] == alt[k].get("richtige_antwort")
            o2 = neu[k]["antwortbuchstabe"] == neu[k].get("richtige_antwort")
            if o1 and not o2:
                b += 1
            elif o2 and not o1:
                c += 1
        print(f"  richtig->falsch: {b}   falsch->richtig: {c}   "
              f"McNemar p = {mcnemar(b, c):.4f}")

    print("\n" + "=" * 96)


if __name__ == "__main__":
    main()