# -*- coding: utf-8 -*-
"""vergleich_fragen.py — Trefferquote derselben FRAGEN: Hauptserie vs. Nachbefragung.

Statt dieselben Records zu vergleichen (die in der Hauptserie per Definition
leer waren), werden hier dieselben Fragen betrachtet: Wie oft beantwortete das
Modell diese Fragen in der Hauptserie richtig (in den Wiederholungen, in denen
es durchkam) — und wie oft in der Nachbefragung mit 4000 Tokens?

Verwendung:
    python vergleich_fragen.py
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def load_jsonl(path):
    if not path.exists():
        sys.exit(f"Datei nicht gefunden: {path}")
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def fkey(r):
    """Frage-Schluessel: Fach + Item + Ton."""
    return (r.get("fach") or r.get("subject"),
            int(r.get("fragen_id", r.get("item_id"))),
            r.get("ton"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", type=Path, default=Path("results/token_split.jsonl"))
    ap.add_argument("--run", type=Path, default=Path("results/claude_full.jsonl"))
    ap.add_argument("--budget", type=int, default=4000)
    args = ap.parse_args()

    split = [r for r in load_jsonl(args.split) if r.get("budget") == args.budget]
    run = load_jsonl(args.run)

    if not split:
        sys.exit(f"Keine Records mit budget={args.budget} in {args.split}")

    # Hauptserie nach Frage gruppieren
    hs = defaultdict(list)
    for r in run:
        if r.get("status") != "ok":
            continue
        hs[fkey(r)].append(r)

    # Nachbefragung nach Frage gruppieren
    nb = defaultdict(list)
    for r in split:
        nb[fkey(r)].append(r)

    fragen = set(nb) & set(hs)
    print("=" * 92)
    print(f"Fragen-Vergleich: Hauptserie (200 Tokens) vs. Nachbefragung ({args.budget} Tokens)")
    print("=" * 92)
    print(f"Fragen in der Nachbefragung : {len(nb)}")
    print(f"davon auch in der Hauptserie: {len(fragen)}")
    print(f"Nachbefragungs-Records      : {len(split)}")

    # ---- 1. Je Ton
    print(f"\n{'-' * 92}")
    print("1) Trefferquote je Ton — dieselben Fragen")
    print(f"{'-' * 92}")
    print(f"{'Ton':<13}{'Fragen':>8}{'HS ausw.':>10}{'HS korr':>9}{'HS %':>8}"
          f"{'NB ausw.':>10}{'NB korr':>9}{'NB %':>8}{'Diff pp':>9}")

    gesamt = {"hs_n": 0, "hs_k": 0, "nb_n": 0, "nb_k": 0}
    for ton in ("neutral", "very_polite", "very_rude"):
        fs = {f for f in fragen if f[2] == ton}
        hs_n = hs_k = nb_n = nb_k = 0
        for f in fs:
            for r in hs[f]:
                if r.get("antwortbuchstabe"):
                    hs_n += 1
                    hs_k += 1 if r["antwortbuchstabe"] == r.get("richtige_antwort") else 0
            for r in nb[f]:
                if r.get("buchstabe"):
                    nb_n += 1
                    nb_k += 1 if r["buchstabe"] == r.get("richtige_antwort") else 0
        hq = 100 * hs_k / hs_n if hs_n else 0
        nq = 100 * nb_k / nb_n if nb_n else 0
        gesamt["hs_n"] += hs_n; gesamt["hs_k"] += hs_k
        gesamt["nb_n"] += nb_n; gesamt["nb_k"] += nb_k
        print(f"{ton:<13}{len(fs):>8}{hs_n:>10}{hs_k:>9}{hq:>7.1f}%"
              f"{nb_n:>10}{nb_k:>9}{nq:>7.1f}%{nq - hq:>+9.1f}")

    if gesamt["hs_n"] and gesamt["nb_n"]:
        h = 100 * gesamt["hs_k"] / gesamt["hs_n"]
        b = 100 * gesamt["nb_k"] / gesamt["nb_n"]
        print(f"{'GESAMT':<13}{len(fragen):>8}{gesamt['hs_n']:>10}"
              f"{gesamt['hs_k']:>9}{h:>7.1f}%{gesamt['nb_n']:>10}"
              f"{gesamt['nb_k']:>9}{b:>7.1f}%{b - h:>+9.1f}")

    # ---- 2. Nur Fragen, die in der HS AUSWERTBAR waren
    print(f"\n{'-' * 92}")
    print("2) Nur Fragen mit mind. einer auswertbaren HS-Antwort")
    print(f"{'-' * 92}")
    print(f"{'Ton':<13}{'Fragen':>8}{'HS %':>8}{'NB %':>8}{'Diff pp':>9}{'HS n':>7}{'NB n':>7}")
    for ton in ("neutral", "very_polite", "very_rude"):
        fs = [f for f in fragen if f[2] == ton
              and any(r.get("antwortbuchstabe") for r in hs[f])]
        if not fs:
            continue
        hs_k = hs_n = nb_k = nb_n = 0
        for f in fs:
            for r in hs[f]:
                if r.get("antwortbuchstabe"):
                    hs_n += 1
                    hs_k += 1 if r["antwortbuchstabe"] == r.get("richtige_antwort") else 0
            for r in nb[f]:
                if r.get("buchstabe"):
                    nb_n += 1
                    nb_k += 1 if r["buchstabe"] == r.get("richtige_antwort") else 0
        hq = 100 * hs_k / hs_n if hs_n else 0
        nq = 100 * nb_k / nb_n if nb_n else 0
        print(f"{ton:<13}{len(fs):>8}{hq:>7.1f}%{nq:>7.1f}%{nq - hq:>+9.1f}"
              f"{hs_n:>7}{nb_n:>7}")

    # ---- 3. Trefferquote der Nachbefragung nach HS-Auswertbarkeit
    print(f"\n{'-' * 92}")
    print("3) Wie gut ist die Nachbefragung, je nachdem ob die Frage in der HS aufging?")
    print(f"{'-' * 92}")
    gruppen = {"HS hatte Antwort": [], "HS immer abgebrochen": []}
    for f in fragen:
        hatte = any(r.get("antwortbuchstabe") for r in hs[f])
        key = "HS hatte Antwort" if hatte else "HS immer abgebrochen"
        for r in nb[f]:
            if r.get("buchstabe"):
                gruppen[key].append(r["buchstabe"] == r.get("richtige_antwort"))
    for k, v in gruppen.items():
        if v:
            print(f"  {k:<24}{len(v):>5} Faelle   {100 * sum(v) / len(v):>5.1f} % richtig")
        else:
            print(f"  {k:<24}  keine Faelle")

    # ---- 4. Kernaussage
    print(f"\n{'-' * 92}")
    print("4) Kernaussage")
    print(f"{'-' * 92}")
    if gesamt["hs_n"] and gesamt["nb_n"]:
        h = 100 * gesamt["hs_k"] / gesamt["hs_n"]
        b = 100 * gesamt["nb_k"] / gesamt["nb_n"]
        d = b - h
        print(f"  Hauptserie (200 Tok.)   : {h:.1f} %  (n={gesamt['hs_n']})")
        print(f"  Nachbefragung ({args.budget} Tok.): {b:.1f} %  (n={gesamt['nb_n']})")
        print(f"  Differenz               : {d:+.1f} pp\n")
        if abs(d) < 3:
            print("  -> Konsistent. Die Nachbefragung reproduziert den Schwierigkeitsgrad")
            print("     dieser Fragen. Die ~72 % sind echt, nicht Artefakt.")
        elif d < 0:
            print("  -> Die Nachbefragung liegt NIEDRIGER als die Hauptserie.")
            print("     Mehr Budget macht die Antworten nicht besser - im Gegenteil.")
            print("     Moegliche Ursache: Zweitaufruf ohne Kontext, andere Samplingsituation.")
        else:
            print("  -> Die Nachbefragung liegt HOEHER als die Hauptserie.")
            print("     Mehr Budget rettet nicht nur das Format, sondern auch Inhalt.")


if __name__ == "__main__":
    main()