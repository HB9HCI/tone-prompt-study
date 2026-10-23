# -*- coding: utf-8 -*-
"""list_unparsed.py — zeigt alle Records mit antwortbuchstabe=null,
die aber ausführlichen Text enthalten. Wiederholungen ausgeschlossen
(pro Frage/Ton wird nur die erste solche Antwort gezeigt).

Verwendung:
    python list_unparsed.py results\\claude_full.jsonl
    python list_unparsed.py results\\claude_full.jsonl --out unparsed.txt
    python list_unparsed.py results\\claude_full.jsonl --min-tokens 5
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    ap.add_argument("--min-tokens", type=int, default=5,
                    help="Mindestzahl output_tokens, damit 'ausführlich' gilt")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--show", type=int, default=50, help="max. Ausgabe auf der Konsole")
    args = ap.parse_args()

    seen = defaultdict(int)      # (fach, fragen_id, ton) -> Anzahl gesehen
    rows = []
    stats = {"total": 0, "null": 0, "empty": 0, "short": 0, "verbose": 0}

    with args.path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            stats["total"] += 1
            if r.get("status") != "ok" or r.get("antwortbuchstabe"):
                continue
            stats["null"] += 1
            raw = (r.get("rohantwort") or "").strip()
            if not raw:
                stats["empty"] += 1
                continue
            if (r.get("output_tokens") or 0) < args.min_tokens:
                stats["short"] += 1
                continue
            stats["verbose"] += 1

            key = (r.get("fach"), r.get("fragen_id"), r.get("ton"))
            seen[key] += 1
            if seen[key] > 1:        # Wiederholung -> überspringen
                continue
            rows.append({
                "fach": r.get("fach"),
                "fragen_id": r.get("fragen_id"),
                "ton": r.get("ton"),
                "wiederholung": r.get("wiederholung"),
                "out_tok": r.get("output_tokens"),
                "finish": r.get("finish_reason"),
                "richtig": r.get("richtige_antwort"),
                "text": raw,
            })

    print(f"Records gesamt:        {stats['total']:>7}")
    print(f"davon antwortbuchstabe=null: {stats['null']:>7}")
    print(f"  leer (kein Text):    {stats['empty']:>7}")
    print(f"  zu kurz (<{args.min_tokens} tok):   {stats['short']:>7}")
    print(f"  ausführlich:         {stats['verbose']:>7}")
    print(f"  unique (Frage/Ton):  {len(rows):>7}\n")

    print(f"{'Fach':<22}{'ID':>6}{'Ton':<12}{'tok':>5}{'finish':>9}{'richtig':>9}")
    print("-" * 100)
    for r in rows[:args.show]:
        print(f"{r['fach']:<22}{r['fragen_id']:>6}{r['ton']:<12}{r['out_tok']:>5}"
              f"{str(r['finish']):>9}{str(r['richtig']):>9}")
        print(f"   {r['text'][:180]!r}")
    if len(rows) > args.show:
        print(f"\n... {len(rows) - args.show} weitere")

    if args.out:
        with args.out.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"\nVollständige Liste: {args.out}")


if __name__ == "__main__":
    main()