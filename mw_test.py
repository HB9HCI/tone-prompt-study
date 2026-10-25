# -*- coding: utf-8 -*-
"""mw_test.py — Mann-Whitney-Tests auf reasoning_tokens zwischen den vier Armen.

Fragen:
  (a) Verbraucht ein Arm mehr Reasoning als Neutral? (MW-Test, alle Records)
  (b) Und unter den Antworten, die UEBERHAUPT Reasoning haben (> 0)?
  (c) Anteil der Antworten mit Reasoning > 0 je Arm (2-Proportionen-z)
  (d) Bootstrap-Konfidenzintervall fuer die Mittelwertdifferenz

Keine scipy-Abhaengigkeit; Normalapproximation mit Korrektur fuer Bindungen.

Verwendung:
    python mw_test.py
    python mw_test.py --fair results/claude_fair.jsonl --ref neutral
"""

import argparse
import json
import math
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ARME = ["neutral", "very_polite", "very_rude", "threat"]
LABEL = {"neutral": "Neutral", "very_polite": "Polite",
         "very_rude": "Rude", "threat": "Threat"}


def load(path):
    if not Path(path).exists():
        sys.exit(f"Datei nicht gefunden: {path}")
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def mannwhitney(a, b):
    """U-Test mit Normalapproximation und Bindungskorrektur. Liefert (u1, z, p)."""
    n1, n2 = len(a), len(b)
    if n1 == 0 or n2 == 0:
        return None, None, None
    combined = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    ranks = [0.0] * len(combined)
    i = 0
    while i < len(combined):
        j = i
        while j + 1 < len(combined) and combined[j + 1][0] == combined[i][0]:
            j += 1
        avg_rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        i = j + 1
    r1 = sum(r for r, (_, grp) in zip(ranks, combined) if grp == 0)
    u1 = r1 - n1 * (n1 + 1) / 2.0
    mu = n1 * n2 / 2.0
    vals = defaultdict(int)
    for v, _ in combined:
        vals[v] += 1
    tie_term = sum(t ** 3 - t for t in vals.values())
    n = n1 + n2
    var = n1 * n2 / 12.0 * ((n + 1) - tie_term / (n * (n - 1)))
    if var == 0:
        return u1, 0.0, 1.0
    z = (u1 - mu) / math.sqrt(var)   # positiv => Arm a hoeher
    p = math.erfc(abs(z) / math.sqrt(2))
    return u1, z, p


def two_prop_z(x1, n1, x2, n2):
    p1, p2 = x1 / n1, x2 / n2
    pp = (x1 + x2) / (n1 + n2)
    se = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
    if se == 0:
        return 0.0, 1.0
    z = (p1 - p2) / se
    return z, math.erfc(abs(z) / math.sqrt(2))


def bootstrap_diff_ci(a, b, n_boot=2000, seed=42):
    """95-%-CI der Mittelwertdifferenz (a - b) per Bootstrap."""
    rng = random.Random(seed)
    diffs = []
    la, lb = len(a), len(b)
    for _ in range(n_boot):
        ma = statistics.mean(a[rng.randrange(la)] for _ in range(la))
        mb = statistics.mean(b[rng.randrange(lb)] for _ in range(lb))
        diffs.append(ma - mb)
    diffs.sort()
    return diffs[int(0.025 * (n_boot - 1))], diffs[int(0.975 * (n_boot - 1))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fair", default="results/claude_fair.jsonl")
    ap.add_argument("--ref", default="neutral")
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    records = [r for r in load(args.fair) if r.get("status") == "ok"]
    vals = defaultdict(list)
    for r in records:
        vals[r.get("ton")].append(r.get("reasoning_tokens") or 0)

    if not vals.get(args.ref):
        sys.exit(f"Referenzarm {args.ref} nicht gefunden.")

    ref_all = vals[args.ref]
    ref_pos = [v for v in ref_all if v > 0]
    share_ref = sum(1 for v in ref_all if v > 0) / len(ref_all)

    print("=" * 96)
    print(f"MANN-WHITNEY-TESTS: reasoning_tokens (Referenz = {LABEL[args.ref]})")
    print("=" * 96)
    print(f"Records gesamt: {len(records)}")

    # --- Beschreibung
    print(f"\n{'-' * 96}")
    print("Beschreibung je Arm")
    print(f"{'-' * 96}")
    print(f"{'Arm':<13}{'n':>7}{'mean':>9}{'median':>9}{'p90':>7}"
          f"{'max':>7}{'Anteil >0':>11}")
    for ton in ARME:
        v = vals.get(ton) or []
        if not v:
            continue
        sv = sorted(v)
        p90 = sv[int(0.9 * (len(sv) - 1))]
        share = sum(1 for x in v if x > 0) / len(v)
        print(f"{LABEL[ton]:<13}{len(v):>7}{statistics.mean(v):>9.1f}"
              f"{statistics.median(v):>9.1f}{p90:>7}{max(v):>7}"
              f"{100*share:>10.1f}%")

    # --- (a) MW alle Records
    print(f"\n{'-' * 96}")
    print(f"a) MW-Test, alle Records (Referenz {LABEL[args.ref]})")
    print(f"{'-' * 96}")
    print(f"{'Vergleich':<26}{'n1':>7}{'n2':>7}{'mean Diff':>11}"
          f"{'z':>8}{'p':>10}{'Bootstrap 95% CI':>22}")
    for ton in ARME:
        if ton == args.ref:
            continue
        v = vals.get(ton) or []
        if not v:
            continue
        u, z, p = mannwhitney(ref_all, v)
        d = statistics.mean(v) - statistics.mean(ref_all)
        lo, hi = bootstrap_diff_ci(v, ref_all, args.n_boot, args.seed)
        sig = " *" if p < 0.05 else ""
        print(f"{LABEL[ton]+' - Neutral':<26}{len(ref_all):>7}{len(v):>7}"
              f"{d:>+11.1f}{z:>8.2f}{p:>10.4f}{sig}"
              f"  [{lo:>+7.1f}, {hi:>+7.1f}]")

    # --- (b) MW nur Reasoning > 0
    print(f"\n{'-' * 96}")
    print("b) MW-Test, nur Records mit reasoning_tokens > 0")
    print(f"{'-' * 96}")
    print(f"{'Vergleich':<26}{'n1':>7}{'n2':>7}{'mean Diff':>11}"
          f"{'z':>8}{'p':>10}")
    for ton in ARME:
        if ton == args.ref:
            continue
        v = [x for x in (vals.get(ton) or []) if x > 0]
        if not v:
            continue
        u, z, p = mannwhitney(ref_pos, v)
        d = statistics.mean(v) - statistics.mean(ref_pos)
        print(f"{LABEL[ton]+' - Neutral':<26}{len(ref_pos):>7}{len(v):>7}"
              f"{d:>+11.1f}{z:>8.2f}{p:>10.4f}")

    # --- (c) Anteilstest
    print(f"\n{'-' * 96}")
    print("c) Anteil der Antworten mit Reasoning > 0 (2-Proportionen-z)")
    print(f"{'-' * 96}")
    print(f"{'Vergleich':<26}{'Anteil A':>11}{'Anteil B':>11}"
          f"{'Diff pp':>10}{'z':>8}{'p':>10}")
    for ton in ARME:
        if ton == args.ref:
            continue
        v = vals.get(ton) or []
        if not v:
            continue
        share = sum(1 for x in v if x > 0) / len(v)
        z, p = two_prop_z(share * len(v), len(v),
                          share_ref * len(ref_all), len(ref_all))
        print(f"{LABEL[ton]+' - Neutral':<26}{100*share_ref:>10.1f}%"
              f"{100*share:>10.1f}%{100*(share-share_ref):>+9.1f}"
              f"{z:>8.2f}{p:>10.4f}")

    # --- Interpretationshilfe
    print(f"\n{'-' * 96}")
    print("Interpretationshilfe")
    print(f"{'-' * 96}")
    print("  (a) prueft die GESAMTE Verteilung inkl. Nullen — der zentrale Test.")
    print("  (b) prueft nur die INTENSITAET bei aktivem Reasoning.")
    print("  (c) prueft die HAEUFIGKEIT von Reasoning (Nullen vs. nicht-Nullen).")
    print("  Bei zweigipfliger Verteilung kann (a) signifikant sein, (b) nicht:")
    print("  dann unterscheidet sich die HAEUFIGKEIT, nicht die LAENGE.")
    print("  Bonferroni bei 3 Vergleichen: p < 0.0167 statt 0.05.")


if __name__ == "__main__":
    main()