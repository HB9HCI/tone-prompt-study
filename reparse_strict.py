# -*- coding: utf-8 -*-
"""reparse_strict.py — S2-eng: konservatives Nachparsing nicht auswertbarer Antworten.

Aendert NICHTS an der Eingabedatei. Schreibt nur einen Bericht und optional
eine JSONL mit den geretteten Faellen zur Kontrolle.

Verwendung:
    python reparse_strict.py results\\claude_full.jsonl
    python reparse_strict.py results\\claude_full.jsonl --out gerettet.jsonl
    python reparse_strict.py results\\claude_full.jsonl --apply
"""

import argparse
import json
import re
from pathlib import Path

# --- Signalwoerter: Antwortbuchstabe steht ausdruecklich als Ergebnis da
SIGNALS = [
    r"\banswer\s+is\s*[:\-]?\s*\(?([A-D])\)?\.?\s*$",
    r"\banswer\s*[:\-]\s*\(?([A-D])\)?\.?\s*$",
    r"\bcorrect\s+(?:option|answer|choice)\s+is\s*[:\-]?\s*\(?([A-D])\)?\.?\s*$",
    r"\bthe\s+correct\s+answer\s+is\s*\(?([A-D])\)?\.?\s*$",
    r"\boption\s+\(?([A-D])\)?\s+is\s+(?:the\s+)?correct",
    r"\b(?:therefore|thus|hence),?\s*\(?([A-D])\)?\.?\s*$",
    r"^(?:therefore|thus|hence),?\s*\(?([A-D])\)?\.?\s*$",
    r"\bantwort\s+ist\s*[:\-]?\s*\(?([A-D])\)?\.?\s*$",
]
SIGNAL_RE = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in SIGNALS]

# --- Freistehender Buchstabe am Textende (max. 12 Zeichen Resttext erlaubt)
TAIL_RE = re.compile(r"(?:^|[\s\n])\(?([A-D])\)?[\s.!,]*$")

# --- Ausschluesse: Buchstabe klar als Optionszitat, nicht als Antwort
#     z.B. "A) ...", "A. ...", "(A) something", "A and B are false"
OPTION_QUOTE_RE = re.compile(r"^\s*\(?([A-D])[\).:]\s+\S", re.MULTILINE)
MULTI_LETTER_RE = re.compile(r"\b[A-D]\b\s*(?:and|und|,|/)\s*\b[A-D]\b", re.IGNORECASE)


def strip_tail(text: str, limit: int = 40) -> str:
    """Nur den Schluss des Textes betrachten."""
    t = text.rstrip()
    return t[-limit:] if len(t) > limit else t


def s2_eng(text: str) -> tuple[str | None, str]:
    """Gibt (Buchstabe, Begruendung) zurueck. Buchstabe None = nicht gerettet."""
    if not isinstance(text, str):
        return None, "kein Text"
    t = text.strip()
    if not t:
        return None, "leer"

    tail = strip_tail(t, 40)

    # 1) Signalwoerter am Schluss
    for rx in SIGNAL_RE:
        m = rx.search(tail)
        if m:
            return m.group(1).upper(), f"signal:{rx.pattern[:40]}"

    # 2) Freistehender Buchstabe ganz am Ende
    m = TAIL_RE.search(tail)
    if m:
        letter = m.group(1).upper()
        # Ausschluss: der Buchstabe steht als Optionszitat am Zeilenanfang
        if OPTION_QUOTE_RE.search(t):
            return None, "optionszitat erkannt"
        if MULTI_LETTER_RE.search(t):
            return None, "mehrere Buchstaben (A and B ...)"
        return letter, "tail"

    return None, "kein Muster"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    ap.add_argument("--out", type=Path, default=None,
                    help="JSONL mit den geretteten Faellen zur Kontrolle")
    ap.add_argument("--apply", action="store_true",
                    help="Aenderungen in eine neue Datei schreiben (*.reparsed.jsonl)")
    ap.add_argument("--show", type=int, default=30)
    args = ap.parse_args()

    stats = {"total": 0, "ok": 0, "null": 0, "empty": 0, "rescued": 0, "rejected": 0}
    rescued_rows = []
    reasons = {}

    with args.path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            stats["total"] += 1
            if r.get("status") != "ok":
                continue
            stats["ok"] += 1
            if r.get("antwortbuchstabe"):
                continue
            stats["null"] += 1
            raw = (r.get("rohantwort") or "").strip()
            if not raw:
                stats["empty"] += 1
                continue

            letter, why = s2_eng(raw)
            reasons[why] = reasons.get(why, 0) + 1
            if letter:
                stats["rescued"] += 1
                rescued_rows.append({
                    "fach": r.get("fach"), "fragen_id": r.get("fragen_id"),
                    "ton": r.get("ton"), "wiederholung": r.get("wiederholung"),
                    "gerettet": letter, "richtig": r.get("richtige_antwort"),
                    "treffer": letter == r.get("richtige_antwort"),
                    "grund": why, "finish": r.get("finish_reason"),
                    "text": raw,
                })
            else:
                stats["rejected"] += 1

    print(f"Records:            {stats['total']}")
    print(f"  status ok:        {stats['ok']}")
    print(f"  davon null:       {stats['null']}")
    print(f"    leer:           {stats['empty']}")
    print(f"    gerettet (S2):  {stats['rescued']}")
    print(f"    verworfen:      {stats['rejected']}")
    if stats["null"]:
        rate = stats["rescued"] / stats["null"]
        print(f"  Rettungsquote:    {100 * rate:.1f} % der null-Faelle")

    if rescued_rows:
        hits = sum(1 for r in rescued_rows if r["treffer"])
        print(f"\nTrefferquote der Geretteten (vs. richtige_antwort): "
              f"{hits}/{len(rescued_rows)} = {100 * hits / len(rescued_rows):.1f} %")
        print("  (Vergleich: Gesamt-Accuracy der parsebaren Antworten lag bei ~96 %)")

    print(f"\nGruende:")
    for why, n in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"  {why:<40}{n:>7}")

    print(f"\n{'-' * 80}")
    print("Kontrollstichprobe (jede Zeile: gelesener Buchstabe | richtig | Textende)")
    print(f"{'-' * 80}")
    for r in rescued_rows[:args.show]:
        tail = r["text"].strip()[-70:]
        mark = "OK " if r["treffer"] else "X  "
        print(f"{mark}{r['fach']:<20}{r['fragen_id']:>5} {r['ton']:<12} "
              f"gelesen={r['gerettet']} richtig={r['richtig']}  ...{tail!r}")

    if args.out:
        with args.out.open("w", encoding="utf-8") as f:
            for r in rescued_rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"\nKontrolldatei: {args.out}")

    print("\nNaechster Schritt: Kontrollstichprobe pruefen.")
    print("Nur wenn die geretteten Buchstaben plausibel sind: --apply verwenden.")


if __name__ == "__main__":
    main()