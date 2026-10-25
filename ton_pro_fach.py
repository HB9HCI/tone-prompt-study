# -*- coding: utf-8 -*-
"""ton_pro_fach.py — Toneffekt innerhalb jedes Fachs.

Zeigt je Fach: richtig/falsch pro Tonbedingung, Quote, Spread und alle drei
paarweisen Differenzen (N-P, N-R, P-R) in Prozentpunkten. Darunter
Chi-Quadrat je Fach (3x2: Ton x richtig/falsch) plus paarweise p-Werte.

Verwendung:
    python ton_pro_fach.py results\\claude_full.jsonl
    python ton_pro_fach.py results\\claude_full.jsonl --csv results\\ton_pro_fach.csv
"""

import argparse
import csv
import json
import math
import sys
from pathlib import Path

TONE_ORDER = ["neutral", "very_polite", "very_rude"]
TONE_LABEL = {"neutral": "Neutral", "very_polite": "Polite", "very_rude": "Rude"}


def chi2_2xk(table):
    """Chi-Quadrat ohne Korrektur fuer k x 2 Tafel; gibt (chi2, df)."""
    rows = len(table)
    row_sum = [sum(r) for r in table]
    col_sum = [sum(table[i][j] for i in range(rows)) for j in range(2)]
    total = sum(row_sum)
    chi2 = 0.0
    for i in range(rows):
        for j in range(2):
            exp = row_sum[i] * col_sum[j] / total
            if exp > 0:
                chi2 += (table[i][j] - exp) ** 2 / exp
    return chi2, (rows - 1)


def chi2_sf(chi2, df):
    """Ueberlebensfunktion der Chi-Quadrat-Verteilung."""
    if chi2 <= 0:
        return 1.0
    a, x = df / 2.0, chi2 / 2.0

    def lower_gamma_reg(a, x):
        if x < a + 1:
            term = 1.0 / a
            total = term
            n = a
            for _ in range(300):
                n += 1
                term *= x / n
                total += term
                if abs(term) < abs(total) * 1e-12:
                    break
            return total * math.exp(-x + a * math.log(x) - math.lgamma(a))
        tiny = 1e-300
        b = x + 1 - a
        c = 1 / tiny
        d = 1 / b if b != 0 else 1 / tiny
        h = d
        for i in range(1, 300):
            an = -i * (i - a)
            b += 2
            d = an * d + b
            if abs(d) < tiny:
                d = tiny
            c = b + an / c
            if abs(c) < tiny:
                c = tiny
            d = 1 / d
            delta = d * c
            h *= delta
            if abs(delta - 1) < 1e-12:
                break
        return 1 - math.exp(-x + a * math.log(x) - math.lgamma(a)) * h

    return 1 - lower_gamma_reg(a, x)


def pct(x):
    return f"{100 * x:.2f} %"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", type=Path)
    ap.add_argument("--csv", type=Path, default=None)
    args = ap.parse_args()

    if not args.run.exists():
        sys.exit(f"Datei nicht gefunden: {args.run}")

    records = []
    with args.run.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                if r.get("status") == "ok" and r.get("antwortbuchstabe"):
                    records.append(r)

    faecher = sorted({r.get("fach") for r in records})

    print("=" * 122)
    print("Toneffekt innerhalb jedes Fachs (nur auswertbare Antworten, strikt)")
    print("=" * 122)
    print(f"{'Fach':<26}{'Neutral':>20}{'Polite':>20}{'Rude':>20}"
          f"{'Spread':>10}{'N-P':>8}{'N-R':>8}{'P-R':>8}")
    print("-" * 122)

    gesamt = {}
    rows_csv = []

    for fach in faecher:
        zeile = f"{fach:<26}"
        qu = []
        counts = {}
        for tone in TONE_ORDER:
            rs = [r for r in records if r.get("fach") == fach and r.get("ton") == tone]
            cor = sum(1 for r in rs if r.get("korrekt"))
            n = len(rs)
            q = cor / n if n else 0.0
            qu.append(q)
            counts[tone] = (cor, n - cor, n)
            zeile += f"{f'{cor}:{n - cor} ({pct(q)})':>20}"
        spread = (max(qu) - min(qu)) * 100
        d_np = (qu[1] - qu[0]) * 100
        d_nr = (qu[2] - qu[0]) * 100
        d_pr = (qu[2] - qu[1]) * 100
        zeile += f"{spread:>9.2f}pp{d_np:>+8.2f}{d_nr:>+8.2f}{d_pr:>+8.2f}"
        print(zeile)
        gesamt[fach] = counts
        rows_csv.append([fach, counts["neutral"][2], counts["neutral"][0],
                         counts["very_polite"][0], counts["very_rude"][0],
                         f"{qu[0]:.4f}", f"{qu[1]:.4f}", f"{qu[2]:.4f}",
                         f"{spread:.2f}", f"{d_np:.2f}", f"{d_nr:.2f}", f"{d_pr:.2f}"])

    print("-" * 122)
    zeile = f"{'GESAMT':<26}"
    qu = []
    allc = {}
    for tone in TONE_ORDER:
        rs = [r for r in records if r.get("ton") == tone]
        cor = sum(1 for r in rs if r.get("korrekt"))
        n = len(rs)
        q = cor / n if n else 0.0
        qu.append(q)
        allc[tone] = (cor, n - cor, n)
        zeile += f"{f'{cor}:{n - cor} ({pct(q)})':>20}"
    spread = (max(qu) - min(qu)) * 100
    d_np = (qu[1] - qu[0]) * 100
    d_nr = (qu[2] - qu[0]) * 100
    d_pr = (qu[2] - qu[1]) * 100
    zeile += f"{spread:>9.2f}pp{d_np:>+8.2f}{d_nr:>+8.2f}{d_pr:>+8.2f}"
    print(zeile)
    rows_csv.append(["GESAMT", allc["neutral"][2], allc["neutral"][0],
                     allc["very_polite"][0], allc["very_rude"][0],
                     f"{qu[0]:.4f}", f"{qu[1]:.4f}", f"{qu[2]:.4f}",
                     f"{spread:.2f}", f"{d_np:.2f}", f"{d_nr:.2f}", f"{d_pr:.2f}"])

    print(f"\n{'-' * 122}")
    print("Chi-Quadrat je Fach (3x2: Ton x richtig/falsch)")
    print(f"{'-' * 122}")

    def paar(c, a, b):
        t2 = [[c[a][0], c[a][1]], [c[b][0], c[b][1]]]
        c2, d2 = chi2_2xk(t2)
        return chi2_sf(c2, d2)

    for fach in faecher:
        c = gesamt[fach]
        table = [[c[t][0], c[t][1]] for t in TONE_ORDER]
        chi2, df = chi2_2xk(table)
        p = chi2_sf(chi2, df)
        p_np = paar(c, "neutral", "very_polite")
        p_nr = paar(c, "neutral", "very_rude")
        p_pr = paar(c, "very_polite", "very_rude")
        print(f"{fach:<26}chi2={chi2:>7.2f}  p={p:>9.4g}"
              f"   (N-P p={p_np:.4g}, N-R p={p_nr:.4g}, P-R p={p_pr:.4g})"
              + ("   <-- signifikant" if p < 0.05 else ""))

    print(f"\n{'-' * 122}")
    print("Legende: N-P = Polite minus Neutral, N-R = Rude minus Neutral,")
    print("         P-R = Rude minus Polite (in Prozentpunkten, + = besser).")
    print("Warnung: Bei ~14.000 Records je Fach-Ton-Zelle werden schon Spreads")
    print("von ~1 pp signifikant. Entscheidend ist die Effektgroesse, nicht p.")

    if args.csv:
        with args.csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Fach", "n", "richtig_neutral", "richtig_polite", "richtig_rude",
                        "quote_neutral", "quote_polite", "quote_rude",
                        "spread_pp", "N-P_pp", "N-R_pp", "P-R_pp"])
            w.writerows(rows_csv)
        print(f"\nCSV geschrieben: {args.csv}")


if __name__ == "__main__":
    main()