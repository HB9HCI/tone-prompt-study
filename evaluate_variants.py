# -*- coding: utf-8 -*-
"""evaluate_variants.py — Auswertung strikt vs. nachgeparst, Fokus Auswertbarkeit je Ton."""

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

TONE_ORDER = ["neutral", "very_polite", "very_rude"]
TONE_LABEL = {"neutral": "Neutral", "very_polite": "Very Polite", "very_rude": "Very Rude"}
LETTERS = ["A", "B", "C", "D"]

SIGNALS = [
    r"\banswer\s+is\s*[:\-]?\s*\(?([A-D])\)?\.?\s*$",
    r"\banswer\s*[:\-]\s*\(?([A-D])\)?\.?\s*$",
    r"\bcorrect\s+(?:option|answer|choice)\s+is\s*[:\-]?\s*\(?([A-D])\)?\.?\s*$",
    r"\bthe\s+correct\s+answer\s+is\s*\(?([A-D])\)?\.?\s*$",
    r"\boption\s+\(?([A-D])\)?\s+is\s+(?:the\s+)?correct",
    r"\b(?:therefore|thus|hence),?\s*\(?([A-D])\)?\.?\s*$",
    r"\bantwort\s+ist\s*[:\-]?\s*\(?([A-D])\)?\.?\s*$",
]
SIGNAL_RE = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in SIGNALS]
TAIL_RE = re.compile(r"(?:^|[\s\n])\(?([A-D])\)?[\s.!,]*$")
OPTION_QUOTE_RE = re.compile(r"^\s*\(?([A-D])[\).:]\s+\S", re.MULTILINE)
MULTI_LETTER_RE = re.compile(r"\b[A-D]\b\s*(?:and|und|,|/)\s*\b[A-D]\b", re.IGNORECASE)


def s2_eng(text):
    if not isinstance(text, str):
        return None
    t = text.strip()
    if not t:
        return None
    tail = t[-40:] if len(t) > 40 else t
    for rx in SIGNAL_RE:
        m = rx.search(tail)
        if m:
            return m.group(1).upper()
    m = TAIL_RE.search(tail)
    if m:
        if OPTION_QUOTE_RE.search(t) or MULTI_LETTER_RE.search(t):
            return None
        return m.group(1).upper()
    return None


def wilson(k, n, z=1.959964):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def chi2_table(table):
    rows = len(table)
    cols = 2
    row_sum = [sum(r) for r in table]
    col_sum = [sum(table[i][j] for i in range(rows)) for j in range(cols)]
    total = sum(row_sum)
    chi2 = 0.0
    for i in range(rows):
        for j in range(cols):
            exp = row_sum[i] * col_sum[j] / total
            if exp > 0:
                chi2 += (table[i][j] - exp) ** 2 / exp
    return chi2, (rows - 1) * (cols - 1)


def chi2_sf(chi2, df):
    if chi2 <= 0:
        return 1.0
    a = df / 2.0
    x = chi2 / 2.0

    def lower_gamma_reg(a, x):
        if x < a + 1:
            term = 1.0 / a
            total = term
            n = a
            for _ in range(200):
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
        for i in range(1, 200):
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
        q = math.exp(-x + a * math.log(x) - math.lgamma(a)) * h
        return 1 - q

    return 1 - lower_gamma_reg(a, x)


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


def prepare(records):
    for r in records:
        if r.get("status") != "ok":
            r["_s2"] = None
            r["_s2_quelle"] = None
            continue
        if r.get("antwortbuchstabe"):
            r["_s2"] = r["antwortbuchstabe"]
            r["_s2_quelle"] = "strikt"
        else:
            letter = s2_eng(r.get("rohantwort") or "")
            r["_s2"] = letter
            r["_s2_quelle"] = "s2" if letter else None
    return records


def block(records, mode):
    key = "antwortbuchstabe" if mode == "strikt" else "_s2"
    res = {}
    for tone in TONE_ORDER:
        rs = [r for r in records if r.get("status") == "ok" and r.get("ton") == tone]
        ps = [r for r in rs if r.get(key)]
        cor = sum(1 for r in ps if r.get(key) == r.get("richtige_antwort"))
        n = len(rs)
        res[tone] = {
            "n": n, "parsed": len(ps), "unparsed": n - len(ps), "correct": cor,
            "parseable": len(ps) / n if n else 0.0,
            "acc_parsed": cor / len(ps) if ps else 0.0,
            "acc_all": cor / n if n else 0.0,
            "ci_parseable": wilson(len(ps), n),
        }
    return res


def print_block(res, title):
    print(f"\n{'-' * 96}")
    print(title)
    print(f"{'-' * 96}")
    print(f"{'Ton':<13}{'n':>7}{'auswertbar':>12}{'Quote':>10}{'95%-KI':>22}{'Acc(parse)':>13}{'Acc(alle)':>12}")
    for tone in TONE_ORDER:
        t = res[tone]
        if t["n"] == 0:
            continue
        lo, hi = t["ci_parseable"]
        print(f"{TONE_LABEL[tone]:<13}{t['n']:>7}{t['parsed']:>12}{pct(t['parseable']):>10}"
              f"{f'{pct(lo)} - {pct(hi)}':>22}{pct(t['acc_parsed']):>13}{pct(t['acc_all']):>12}")


def ratios(res, label):
    print(f"\nVerhaeltnis der Auswertbarkeit ({label}) zu Neutral:")
    basis = res["neutral"]["parseable"] if res["neutral"]["n"] else 0
    print(f"{'Vergleich':<24}{'Quote':>10}{'Delta (pp)':>13}{'Faktor':>10}")
    for tone in ["very_polite", "very_rude"]:
        t = res[tone]
        if t["n"] == 0 or basis == 0:
            continue
        print(f"{TONE_LABEL[tone] + ' / Neutral':<24}{pct(t['parseable']):>10}"
              f"{100 * (t['parseable'] - basis):>+13.2f}{t['parseable'] / basis:>10.3f}")


def test_unparseable(records):
    print(f"\n{'-' * 96}")
    print("Test: unterscheidet sich die Auswertbarkeit zwischen den Tonbedingungen?")
    print(f"{'-' * 96}")
    for mode, label in [("strikt", "strikt"), ("s2", "nachgeparst")]:
        key = "antwortbuchstabe" if mode == "strikt" else "_s2"
        counts, table = {}, []
        for tone in TONE_ORDER:
            rs = [r for r in records if r.get("status") == "ok" and r.get("ton") == tone]
            p = sum(1 for r in rs if r.get(key))
            counts[tone] = (p, len(rs) - p)
            table.append([p, len(rs) - p])
        chi2, df = chi2_table(table)
        pval = chi2_sf(chi2, df)
        print(f"\n  [{label}] 3x2-Tafel (Ton x auswertbar/nicht): chi2={chi2:.2f}, df={df}, p={pval:.4g}"
              + ("   (signifikant)" if pval < 0.05 else ""))
        for other in ["very_polite", "very_rude"]:
            t = [list(counts["neutral"]), list(counts[other])]
            c2, d2 = chi2_table(t)
            p2 = chi2_sf(c2, d2)
            print(f"      Neutral vs. {TONE_LABEL[other]:<12}: chi2={c2:.2f}, p={p2:.4g}"
                  + ("   (signifikant)" if p2 < 0.05 else ""))


def compare_modes(strikt, s2):
    print(f"\n{'-' * 96}")
    print("Effekt der Nachparsing-Stufe")
    print(f"{'-' * 96}")
    print(f"{'Ton':<13}{'ausw. strikt':>14}{'ausw. S2':>12}{'Zuwachs':>10}"
          f"{'Acc p. strikt':>15}{'Acc p. S2':>12}{'Delta':>9}")
    for tone in TONE_ORDER:
        a, b = strikt[tone], s2[tone]
        if a["n"] == 0:
            continue
        print(f"{TONE_LABEL[tone]:<13}{pct(a['parseable']):>14}{pct(b['parseable']):>12}"
              f"{b['parsed'] - a['parsed']:>+10}"
              f"{pct(a['acc_parsed']):>15}{pct(b['acc_parsed']):>12}"
              f"{100 * (b['acc_parsed'] - a['acc_parsed']):>+9.2f}")


def extra_tables(records):
    print(f"\n{'-' * 96}")
    print("Accuracy je Fach (Variante nachgeparst)")
    print(f"{'-' * 96}")
    print(f"{'Fach':<26}{'n':>7}{'auswertbar':>12}{'Quote':>10}{'Acc(parse)':>13}{'Acc(alle)':>12}")
    for subj in sorted({r.get("fach") for r in records if r.get("status") == "ok" and r.get("fach")}):
        rs = [r for r in records if r.get("status") == "ok" and r.get("fach") == subj]
        ps = [r for r in rs if r.get("_s2")]
        cor = sum(1 for r in ps if r["_s2"] == r.get("richtige_antwort"))
        n = len(rs)
        print(f"{subj:<26}{n:>7}{len(ps):>12}{pct(len(ps) / n if n else 0):>10}"
              f"{pct(cor / len(ps) if ps else 0):>13}{pct(cor / n if n else 0):>12}")

    print(f"\n{'-' * 96}")
    print("Antwortverteilung (nachgeparst) — Positionsbias")
    print(f"{'-' * 96}")
    for tone in TONE_ORDER:
        rs = [r for r in records if r.get("status") == "ok" and r.get("ton") == tone and r.get("_s2")]
        c = Counter(r["_s2"] for r in rs)
        total = sum(c.values())
        if not total:
            continue
        cells = "  ".join(f"{L}: {c.get(L, 0):>6} ({pct(c.get(L, 0) / total)})" for L in LETTERS)
        print(f"  {TONE_LABEL[tone]:<13}{cells}")

    print(f"\n{'-' * 96}")
    print("Quelle der Auswertbarkeit")
    print(f"{'-' * 96}")
    for tone in TONE_ORDER:
        rs = [r for r in records if r.get("status") == "ok" and r.get("ton") == tone]
        print(f"  {TONE_LABEL[tone]:<13}strikt: {sum(1 for r in rs if r.get('antwortbuchstabe')):>6}"
              f"   + S2: {sum(1 for r in rs if r.get('_s2_quelle') == 's2'):>5}")


def write_csv(path, strikt, s2):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Variante", "Ton", "n", "auswertbar", "auswertbar_quote",
                    "acc_parsed", "acc_alle", "correct"])
        for label, res in [("strikt", strikt), ("s2", s2)]:
            for tone in TONE_ORDER:
                t = res[tone]
                w.writerow([label, tone, t["n"], t["parsed"], f"{t['parseable']:.4f}",
                            f"{t['acc_parsed']:.4f}", f"{t['acc_all']:.4f}", t["correct"]])
    print(f"\nCSV geschrieben: {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", type=Path)
    ap.add_argument("--csv", type=Path, default=None)
    args = ap.parse_args()

    records = prepare(load(args.run))
    ok = [r for r in records if r.get("status") == "ok"]

    print("=" * 96)
    print(f"Auswertung in zwei Varianten: {args.run}")
    print("=" * 96)
    print(f"Records: {len(records)} | ok: {len(ok)} | Fehler: {len(records) - len(ok)}")

    strikt = block(records, "strikt")
    s2 = block(records, "s2")

    print_block(strikt, "VARIANTE A: strikt")
    ratios(strikt, "strikt")
    print_block(s2, "VARIANTE B: S2-eng nachgeparst")
    ratios(s2, "nachgeparst")

    test_unparseable(records)
    compare_modes(strikt, s2)
    extra_tables(records)

    if args.csv:
        write_csv(args.csv, strikt, s2)


if __name__ == "__main__":
    main()