import json
from collections import Counter, defaultdict
from pathlib import Path

ergebnisse = defaultdict(list)

with Path("results/pilot_10.jsonl").open(encoding="utf-8") as datei:
    for zeile in datei:
        datensatz = json.loads(zeile)
        ergebnisse[datensatz["ton"]].append(datensatz)

for ton, datensaetze in ergebnisse.items():
    antworten = Counter(
        datensatz["antwortbuchstabe"] or "UNGÜLTIG"
        for datensatz in datensaetze
    )
    korrekt = sum(datensatz["korrekt"] for datensatz in datensaetze)
    print(
        f"{ton}: {len(datensaetze)} Antworten; "
        f"korrekt {korrekt}/10; Antworten {dict(antworten)}"
    )
