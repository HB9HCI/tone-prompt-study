# -*- coding: utf-8 -*-
"""evaluate_run.py — Auswertung eines Laufs im Stil der Originalarbeit."""

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

TONE_ORDER = ["neutral", "very_polite", "very_rude"]
TONE_LABEL = {"neutral": "Neutral", "very_polite": "Very Polite", "very_rude": "Very Rude"}
LETTERS = ["A", "B", "C", "D"]


def load(path):
    if not path.exists():
        sys.exit(f"Datei nicht gefunden: {path}")
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def wilson(k, n, z=1.959964):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    total = 0.0
    for i in range(k + 1):
        total += math.comb(n, i)
    return min(1.0, 2 * total / (2 ** n))


def pct(x):
    return f"{100 * x:.1f} %"


def evaluate(records):
    ok = [r for r in records if r.get("status") == "ok"]
    err = [r for r in records if r.get("status") != "ok"]
    parsed = [r for r in ok if r.get("antwortbuchstabe")]
    res = {
        "total": len(records), "ok": len(ok), "error": len(err),
        "parsed": len(parsed), "unparsed": len(ok) - len(parsed),
        "correct": sum(1 for r in parsed if r.get("korrekt")),
        "length": sum(1 for r in ok if r.get("finish_reason") == "length"),
        "empty": sum(1 for r in ok if not (r.get("rohantwort") or "").strip()),
    }
    res["acc_parsed"] = res["correct"] / res["parsed"] if res["parsed"] else 0.0
    res["acc_all"] = res["correct"] / res["ok"] if res["ok"] else 0.0
    res["ci_parsed"] = wilson(res["correct"], res["parsed"])
    res["ci_all"] = wilson(res["correct"], res["ok"])

    by_tone = {}
    for tone in TONE_ORDER:
        rs = [r for r in ok if r.get("ton") == tone]
        ps = [r for r in rs if r.get("antwortbuchstabe")]
        cor = sum(1 for r in ps if r.get("korrekt"))
        by_tone[tone] = {
            "n": len(rs), "parsed": len(ps), "correct": cor,
            "acc_parsed": cor / len(ps) if ps else 0.0,
            "acc_all": cor / len(rs) if rs else 0.0,
            "ci_parsed": wilson(cor, len(ps)),
            "ci_all": wilson(cor, len(rs)),
            "dist": Counter(r.get("antwortbuchstabe") or "—" for r in ps),
        }
    res["by_tone"] = by_tone

    table = defaultdict(dict)
    for r in ok:
        if r.get("antwortbuchstabe"):
            table[(r.get("fragen_id"), r.get("wiederholung"), r.get("fach"))][r.get("ton")] = bool(r.get("korrekt"))

    pairs = {}
    for other in ["very_polite", "very_rude"]:
        b = c = 0
        for d in table.values():
            if "neutral" in d and other in d:
                if d["neutral"] and not d[other]:
                    b += 1
                elif not d["neutral"] and d[other]:
                    c += 1
        pairs[other] = {"b": b, "c": c, "n": b + c, "p": mcnemar_exact(b, c)}
    res["mcnemar"] = pairs

    by_subject = {}
    for subj in sorted({r.get("fach") for r in ok if r.get("fach")}):
        rs = [r for r in ok if r.get("fach") == subj]
        ps = [r for r in rs if r.get("antwortbuchstabe")]
        cor = sum(1 for r in ps if r.get("korrekt"))
        by_subject[subj] = {
            "n": len(rs), "correct": cor,
            "acc_parsed": cor / len(ps) if ps else 0.0,
            "acc_all": cor / len(rs) if rs else 0.0,
        }
    res["by_subject"] = by_subject
    res["dist"] = Counter(r.get("antwortbuchstabe") or "—" for r in parsed)
    return res


def print_report(res, label):
    print(f"\n{'=' * 72}")
    print(f"Auswertung: {label}")
    print(f"{'=' * 72}")
    print(f"Records gesamt: {res['total']} | ok: {res['ok']} | Fehler: {res['error']}")
    print(f"parsebar: {res['parsed']} ({pct(res['parsed'] / max(res['ok'], 1))} der ok) "
          f"| unparsed: {res['unparsed']} | leer: {res['empty']} | finish=length: {res['length']}")

    lo, hi = res["ci_parsed"]
    print(f"\nGesamt-Accuracy (nur parsebare): {res['correct']}/{res['parsed']} = "
          f"{pct(res['acc_parsed'])}  [95%-KI {pct(lo)}-{pct(hi)}]")
    lo, hi = res["ci_all"]
    print(f"Gesamt-Accuracy (alle ok, unparsed = falsch): {res['correct']}/{res['ok']} = "
          f"{pct(res['acc_all'])}  [95%-KI {pct(lo)}-{pct(hi)}]")

    print(f"\n{'-' * 72}")
    print(f"{'Tonbedingung':<14}{'n':>7}{'parsed':>8}{'Acc(parse)':>12}{'95%-KI':>18}{'Acc(alle)':>11}")
    print(f"{'-' * 72}")
    for tone in TONE_ORDER:
        t = res["by_tone"].get(tone)
        if not t or t["n"] == 0:
            continue
        lo, hi = t["ci_parsed"]
        print(f"{TONE_LABEL[tone]:<14}{t['n']:>7}{t['parsed']:>8}"
              f"{pct(t['acc_parsed']):>12}{f'{pct(lo)}-{pct(hi)}':>18}{pct(t['acc_all']):>11}")

    print(f"\nAntwortverteilung je Tonbedingung:")
    for tone in TONE_ORDER:
        t = res["by_tone"].get(tone)
        if not t or t["parsed"] == 0:
            continue
        total = sum(t["dist"].values())
        cells = "  ".join(f"{L}: {t['dist'].get(L, 0)} ({pct(t['dist'].get(L, 0) / total)})" for L in LETTERS)
        invalid = t["dist"].get("—", 0)
        print(f"  {TONE_LABEL[tone]:<12}{cells}" + (f"  [nicht parsebar: {invalid}]" if invalid else ""))

    print(f"\nGepaarte Tests (McNemar, exakt):")
    print(f"{'-' * 72}")
    for other in ["very_polite", "very_rude"]:
        p = res["mcnemar"].get(other)
        if not p or p["n"] == 0:
            print(f"  Neutral vs. {TONE_LABEL[other]:<12}: keine gepaarten Paare")
            continue
        print(f"  Neutral vs. {TONE_LABEL[other]:<12}: b={p['b']:>4}  c={p['c']:>4}  n={p['n']:>4}  p={p['p']:.4f}"
              + ("   (signifikant, alpha=0.05)" if p["p"] < 0.05 else ""))

    print(f"\nAccuracy je Fach:")
    print(f"{'-' * 72}")
    print(f"{'Fach':<28}{'n':>7}{'correct':>9}{'Acc(parse)':>13}{'Acc(alle)':>11}")
    for subj, s in res["by_subject"].items():
        print(f"{subj:<28}{s['n']:>7}{s['correct']:>9}{pct(s['acc_parsed']):>13}{pct(s['acc_all']):>11}")

    print(f"\nAntwortverteilung gesamt (parsebar):")
    total = sum(res["dist"].values())
    for L in LETTERS:
        v = res["dist"].get(L, 0)
        print(f"  {L}: {v:>6} ({pct(v / max(total, 1))})")


def compare_with_ref(res, ref, ref_label):
    print(f"\n{'=' * 72}")
    print(f"Vergleich mit Referenz: {ref_label}")
    print(f"{'=' * 72}")
    print(f"{'Tonbedingung':<14}{'Ref Acc':>10}{'Neu Acc':>10}{'Delta':>10}")
    for tone in TONE_ORDER:
        a = ref["by_tone"].get(tone, {}).get("acc_parsed", 0.0)
        b = res["by_tone"].get(tone, {}).get("acc_parsed", 0.0)
        print(f"{TONE_LABEL[tone]:<14}{pct(a):>10}{pct(b):>10}{f'{100 * (b - a):+.2f} pp':>10}")
    print(f"\nAnteil nicht-parsebarer Antworten:")
    print(f"{'Tonbedingung':<14}{'Ref':>10}{'Neu':>10}")
    for tone in TONE_ORDER:
        t_ref, t_new = ref["by_tone"].get(tone), res["by_tone"].get(tone)
        if not t_ref or not t_new or t_ref["n"] == 0 or t_new["n"] == 0:
            continue
        print(f"{TONE_LABEL[tone]:<14}"
              f"{pct((t_ref['n'] - t_ref['parsed']) / t_ref['n']):>10}"
              f"{pct((t_new['n'] - t_new['parsed']) / t_new['n']):>10}")


def write_csv(path, res):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Kategorie", "Ton", "n", "parsed", "correct", "acc_parsed", "ci_low", "ci_high", "acc_all"])
        for tone in TONE_ORDER:
            t = res["by_tone"].get(tone)
            if not t:
                continue
            lo, hi = t["ci_parsed"]
            w.writerow(["Gesamt", tone, t["n"], t["parsed"], t["correct"],
                        f"{t['acc_parsed']:.4f}", f"{lo:.4f}", f"{hi:.4f}", f"{t['acc_all']:.4f}"])
        for subj, s in res["by_subject"].items():
            w.writerow(["Fach", subj, s["n"], "", s["correct"], f"{s['acc_parsed']:.4f}", "", "", f"{s['acc_all']:.4f}"])
    print(f"\nCSV geschrieben: {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", type=Path)
    ap.add_argument("--ref", type=Path, default=None)
    ap.add_argument("--csv", type=Path, default=None)
    args = ap.parse_args()

    res = evaluate(load(args.run))
    print_report(res, str(args.run))
    if args.ref:
        compare_with_ref(res, evaluate(load(args.ref)), str(args.ref))
    if args.csv:
        write_csv(args.csv, res)


if __name__ == "__main__":
    main()