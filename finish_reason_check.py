# -*- coding: utf-8 -*-
"""finish_reason_check.py — prueft, WARUM Antworten unauswertbar sind.

Trennt die beiden moeglichen Wege:
  (a) Budget erschoepft    -> finish_reason = length, Text leer/abgeschnitten
  (b) Modell liefert nichts -> finish_reason = stop, Text leer

Zusaetzlich: Token-Verteilung und, falls vorhanden, Reasoning-Tokens.

Verwendung:
    python finish_reason_check.py results\\claude_full.jsonl
"""

import argparse
import json
import statistics
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", type=Path)
    args = ap.parse_args()

    records = [r for r in load(args.run) if r.get("status") == "ok"]
    if not records:
        sys.exit("Keine Records mit status=ok gefunden.")

    print("=" * 100)
    print(f"Diagnose der unauswertbaren Antworten: {args.run}")
    print("=" * 100)
    print(f"Records (status ok): {len(records)}")

    # ---- 1. finish_reason je Ton
    print(f"\n{'-' * 100}")
    print("1) finish_reason je Tonbedingung")
    print(f"{'-' * 100}")
    print(f"{'Ton':<13}{'n':>8}{'stop':>10}{'length':>10}{'sonstige':>10}")
    for tone in TONE_ORDER:
        rs = [r for r in records if r.get("ton") == tone]
        if not rs:
            continue
        c = Counter(str(r.get("finish_reason")) for r in rs)
        stop = c.get("stop", 0)
        length = c.get("length", 0)
        other = len(rs) - stop - length
        print(f"{TONE_LABEL[tone]:<13}{len(rs):>8}{pct(stop / len(rs)):>10}"
              f"{pct(length / len(rs)):>10}{pct(other / len(rs)):>10}")

    # ---- 2. Kreuztabelle
    print(f"\n{'-' * 100}")
    print("2) Auswertbarkeit x finish_reason (alle Toene)")
    print(f"{'-' * 100}")
    print(f"{'finish':<12}{'auswertbar':>14}{'leer':>10}{'Text ohne Buchst.':>20}{'gesamt':>10}")
    groups = defaultdict(lambda: {"parsed": 0, "empty": 0, "text": 0})
    for r in records:
        fr = str(r.get("finish_reason"))
        g = groups[fr]
        raw = (r.get("rohantwort") or "").strip()
        if r.get("antwortbuchstabe"):
            g["parsed"] += 1
        elif not raw:
            g["empty"] += 1
        else:
            g["text"] += 1
    for fr, g in sorted(groups.items(), key=lambda x: -sum(x[1].values())):
        total = sum(g.values())
        print(f"{fr:<12}{g['parsed']:>14}{g['empty']:>10}{g['text']:>20}{total:>10}")

    # ---- 3. Leere Ausfaelle je Ton
    print(f"\n{'-' * 100}")
    print("3) Leere Antworten je Ton — aufgeschluesselt nach finish_reason")
    print(f"{'-' * 100}")
    print(f"{'Ton':<13}{'leer ges.':>12}{'davon length':>15}{'davon stop':>13}{'Quote leer':>12}")
    for tone in TONE_ORDER:
        rs = [r for r in records if r.get("ton") == tone]
        if not rs:
            continue
        empty = [r for r in rs if not (r.get("rohantwort") or "").strip()]
        e_len = sum(1 for r in empty if str(r.get("finish_reason")) == "length")
        e_stop = sum(1 for r in empty if str(r.get("finish_reason")) == "stop")
        print(f"{TONE_LABEL[tone]:<13}{len(empty):>12}{e_len:>15}{e_stop:>13}"
              f"{pct(len(empty) / len(rs)):>12}")

    # ---- 4. Token-Verteilung
    print(f"\n{'-' * 100}")
    print("4) Output-Token je Ton (nur Records mit output_tokens > 0)")
    print(f"{'-' * 100}")
    print(f"{'Ton':<13}{'n':>8}{'mean':>9}{'median':>9}{'p90':>9}{'max':>8}")
    for tone in TONE_ORDER:
        toks = [(r.get("output_tokens") or 0) for r in records
                if r.get("ton") == tone and (r.get("output_tokens") or 0) > 0]
        if not toks:
            continue
        toks.sort()
        p90 = toks[int(len(toks) * 0.9)] if len(toks) > 1 else toks[0]
        print(f"{TONE_LABEL[tone]:<13}{len(toks):>8}{statistics.mean(toks):>9.1f}"
              f"{statistics.median(toks):>9.1f}{p90:>9}{max(toks):>8}")

    # ---- 5. Abgeschnittene
    print(f"\n{'-' * 100}")
    print("5) Abgeschnittene Antworten (length) — Tokenverteilung")
    print(f"{'-' * 100}")
    print(f"{'Ton':<13}{'n':>8}{'mean':>9}{'median':>9}{'p10':>9}")
    for tone in TONE_ORDER:
        toks = [(r.get("output_tokens") or 0) for r in records
                if r.get("ton") == tone and str(r.get("finish_reason")) == "length"]
        if not toks:
            continue
        toks.sort()
        p10 = toks[int(len(toks) * 0.1)] if len(toks) > 1 else toks[0]
        print(f"{TONE_LABEL[tone]:<13}{len(toks):>8}{statistics.mean(toks):>9.1f}"
              f"{statistics.median(toks):>9.1f}{p10:>9}")

    # ---- 6. Reasoning-Tokens
    print(f"\n{'-' * 100}")
    print("6) Reasoning-Tokens (falls der Endpoint sie liefert)")
    print(f"{'-' * 100}")
    found = False
    for tone in TONE_ORDER:
        vals = []
        for r in records:
            if r.get("ton") != tone:
                continue
            det = r.get("output_tokens_details") or r.get("completion_tokens_details")
            if isinstance(det, dict) and "reasoning_tokens" in det:
                vals.append(det.get("reasoning_tokens") or 0)
        if vals:
            found = True
            print(f"  {TONE_LABEL[tone]:<13}n={len(vals):>6}  mean={statistics.mean(vals):>8.1f}"
                  f"  median={statistics.median(vals):>8.1f}  max={max(vals):>6}")
    if not found:
        print("  Keine reasoning_tokens im Record gespeichert.")
        print("  Hinweis: Dafuer muesste run_full.py das Feld mitschreiben:")
        print("    det = getattr(usage, 'completion_tokens_details', None)")
        print("    ... 'reasoning_tokens': getattr(det, 'reasoning_tokens', None)")

    # ---- 7. Befund
    print(f"\n{'-' * 100}")
    print("7) Befund")
    print(f"{'-' * 100}")
    for tone in TONE_ORDER:
        rs = [r for r in records if r.get("ton") == tone]
        if not rs:
            continue
        empty = [r for r in rs if not (r.get("rohantwort") or "").strip()]
        e_len = sum(1 for r in empty if str(r.get("finish_reason")) == "length")
        share = 100 * e_len / len(empty) if empty else 0
        print(f"  {TONE_LABEL[tone]:<13}leere Antworten: {len(empty):>6}"
              f"   davon length: {share:>5.1f} %")
    print("\n  Ueberwiegt 'length' deutlich, ist Budget-Erschoepfung der Weg.")
    print("  Ueberwiegt 'stop', liefert das Modell bewusst keinen Text.")


if __name__ == "__main__":
    main()