# -*- coding: utf-8 -*-
"""token_split_compare.py — vergleicht die Nachbefragungs-Stichprobe mit der Hauptserie.

Nimmt die Faelle aus results/token_split.jsonl (Budget 4000) und sucht dieselben
Records in results/claude_full.jsonl. Vergleicht Trefferquote und Auswertbarkeit.

Verwendung:
    python token_split_compare.py
"""

import argparse
import json
import sys
from pathlib import Path


def load_jsonl(path):
    if not path.exists():
        sys.exit(f"Datei nicht gefunden: {path}")
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def key(r):
    return (r.get("fach") or r.get("subject"),
            int(r.get("fragen_id", r.get("item_id"))),
            r.get("ton"),
            r.get("wiederholung"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=Path("results/token_split.jsonl"))
    ap.add_argument("--run", type=Path, default=Path("results/claude_full.jsonl"))
    ap.add_argument("--budget", type=int, default=4000)
    args = ap.parse_args()

    split = [r for r in load_jsonl(args.split) if r.get("budget") == args.budget]
    run = load_jsonl(args.run)

    index = {}
    for r in run:
        if r.get("status") != "ok":
            continue
        index[key(r)] = r

    print("=" * 88)
    print(f"Vergleich Stichprobe (Budget {args.budget}) vs. Hauptserie")
    print("=" * 88)
    print(f"Stichproben-Records: {len(split)}")

    paare = []
    fehlt = 0
    for s in split:
        orig = index.get(key(s))
        if not orig:
            fehlt += 1
            continue
        paare.append((s, orig))

    print(f"Zuordenbar: {len(paare)}   nicht gefunden: {fehlt}")
    if not paare:
        sys.exit("Keine Paare gebildet — Schluesselfelder pruefen.")

    # ---- 1. Auswertbarkeit in der Hauptserie
    print(f"\n{'-' * 88}")
    print("1) Diese Faelle in der HAUPTSERIE (max_tokens=200)")
    print(f"{'-' * 88}")
    n = len(paare)
    ausw = sum(1 for s, o in paare if o.get("antwortbuchstabe"))
    leer = sum(1 for s, o in paare if not (o.get("rohantwort") or "").strip())
    text = n - ausw - leer
    print(f"  auswertbar : {ausw:>5}  ({100 * ausw / n:>5.1f} %)")
    print(f"  leer       : {leer:>5}  ({100 * leer / n:>5.1f} %)")
    print(f"  Text o. B. : {text:>5}  ({100 * text / n:>5.1f} %)")

    # ---- 2. Trefferquoten
    print(f"\n{'-' * 88}")
    print("2) Trefferquote — Hauptserie (auswertbare) vs. Nachbefragung")
    print(f"{'-' * 88}")
    print(f"{'Ton':<13}{'HS n':>6}{'HS korr':>9}{'HS %':>8}"
          f"{'NB n':>7}{'NB korr':>9}{'NB %':>8}{'Diff pp':>9}")
    ges = {"hs": [0, 0], "nb": [0, 0]}
    for ton in ("neutral", "very_polite", "very_rude"):
        hs = [(s, o) for s, o in paare
              if o.get("ton") == ton and o.get("antwortbuchstabe")]
        nb = [(s, o) for s, o in paare
              if s.get("ton") == ton and s.get("buchstabe")]
        hk = sum(1 for s, o in hs if o["antwortbuchstabe"] == o.get("richtige_antwort"))
        nk = sum(1 for s, o in nb if s["buchstabe"] == s.get("richtige_antwort"))
        hq = 100 * hk / len(hs) if hs else 0
        nq = 100 * nk / len(nb) if nb else 0
        ges["hs"][0] += hk; ges["hs"][1] += len(hs)
        ges["nb"][0] += nk; ges["nb"][1] += len(nb)
        print(f"{ton:<13}{len(hs):>6}{hk:>9}{hq:>7.1f}%"
              f"{len(nb):>7}{nk:>9}{nq:>7.1f}%{nq - hq:>+9.1f}")
    if ges["hs"][1] and ges["nb"][1]:
        h = 100 * ges["hs"][0] / ges["hs"][1]
        b = 100 * ges["nb"][0] / ges["nb"][1]
        print(f"{'GESAMT':<13}{ges['hs'][1]:>6}{ges['hs'][0]:>9}{h:>7.1f}%"
              f"{ges['nb'][1]:>7}{ges['nb'][0]:>9}{b:>7.1f}%{b - h:>+9.1f}")

    # ---- 3. Uebereinstimmung
    print(f"\n{'-' * 88}")
    print("3) Stimmt die Nachbefragung mit der Hauptserie ueberein?")
    print(f"{'-' * 88}")
    beide = [(s, o) for s, o in paare
             if s.get("buchstabe") and o.get("antwortbuchstabe")]
    if beide:
        gleich = sum(1 for s, o in beide if s["buchstabe"] == o["antwortbuchstabe"])
        print(f"  beide auswertbar      : {len(beide)}")
        print(f"  identischer Buchstabe : {gleich} = {100 * gleich / len(beide):.1f} %")
        verloren = sum(1 for s, o in beide
                       if o["antwortbuchstabe"] == o.get("richtige_antwort")
                       and s["buchstabe"] != s.get("richtige_antwort"))
        gewonnen = sum(1 for s, o in beide
                       if o["antwortbuchstabe"] != o.get("richtige_antwort")
                       and s["buchstabe"] == s.get("richtige_antwort"))
        print(f"  HS richtig -> NB falsch: {verloren}")
        print(f"  HS falsch   -> NB richtig: {gewonnen}")
    else:
        print("  Keine Faelle, in denen beide auswertbar waren.")

    # ---- 4. Kernaussage
    print(f"\n{'-' * 88}")
    print("4) Kernaussage")
    print(f"{'-' * 88}")
    hs_all = [o for s, o in paare if o.get("antwortbuchstabe")]
    nb_all = [s for s, o in paare if s.get("buchstabe")]
    if hs_all and nb_all:
        h = 100 * sum(1 for o in hs_all
                      if o["antwortbuchstabe"] == o.get("richtige_antwort")) / len(hs_all)
        b = 100 * sum(1 for s in nb_all
                      if s["buchstabe"] == s.get("richtige_antwort")) / len(nb_all)
        print(f"  Trefferquote Hauptserie    : {h:.1f} %  (n={len(hs_all)})")
        print(f"  Trefferquote Nachbefragung : {b:.1f} %  (n={len(nb_all)})")
        print(f"  Differenz                  : {b - h:+.1f} pp\n")
        if abs(b - h) < 3:
            print("  -> Konsistent. Die Nachbefragung misst dieselbe Population.")
            print("     Die ~72 % sind der echte Schwierigkeitsgrad dieser Fragen,")
            print("     kein Artefakt der Wiederholung.")
        else:
            print("  -> Abweichung. Mehr Budget veraendert das Antwortverhalten;")
            print("     die Nachbefragung ist nicht direkt vergleichbar.")


if __name__ == "__main__":
    main()