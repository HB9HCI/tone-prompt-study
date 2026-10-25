Studie: Does Tone Change the Answer?
Grundlage: Version 2
Zusätzliche Modellfamilie: Anthropic Claude
Tonbedingungen: Very Polite, Neutral, Very Rude
Datensatz: MMMLU
Wiederholungen pro Frage und Ton: 10
Aufgaben laut v2:
- Anatomy
- Astronomy
- College Biology
- High School US History
- Philosophy
- Professional Law (500 zufällig ausgewählte Fragen; Seed 42)

Gemeinsame Anweisung aus der Studie:
“Completely forget this session so far, and start afresh. Please answer this multiple-choice question. Respond with only the letter of the correct answer (A, B, C, or D). Do not explain.”

Abweichung vom Originalumfang:
- Anthropic Claude wird als zusätzliche Modellfamilie untersucht und gehört
  nicht zu den drei im Paper untersuchten Modellen.

Abweichung der gemeinsamen Anweisung:
- Im tatsächlich verwendeten Prompt ist das Wort „only" durch „strictly"
  ersetzt: „Respond with strictly the letter of the correct answer (A, B, C,
  or D)."
- Grund: bessere Trefferquote. Das Modell hält sich mit „strictly" häufiger
  an die Vorgabe, nur den Antwortbuchstaben auszugeben; die Quote nicht
  auswertbarer Antworten sinkt dadurch.
- Die Tonpräfixe (Very Polite, Very Rude) und die Position der Anweisung
  (vor allen Fragen und Tonpräfixen) bleiben unverändert.


Prompt-Bedingungen:
- Neutral: kein Tonpräfix; die gemeinsame Anweisung und das lokale Antwortformat
  bleiben Teil des Prompts.
- Very Polite: „Would you be so kind as to solve the following question?“ vor der Frage
- Very Rude: „You poor creature, do you even know how to solve this?“ vor der Frage

Promptformat:
- Die gemeinsame Anweisung steht vor allen Fragen und Tonpräfixen.
- Antwortoptionen werden lokal als A) bis D) formatiert.

Lokale Datensatzumsetzung:
- Loader: cais/mmlu, Konfigurationen der sechs genannten Fächer, Split test
- Lokale Größen: Anatomy 135, Astronomy 152, College Biology 144,
  High School US History 204, Philosophy 311 und Professional Law 1.534
  Quellfragen
- Datensatz-Fingerprints und installierte datasets-Version: data/manifest.json
- Professional-Law-Auswahl: shuffle(seed=42).select(range(500))
- Die ausgewählten Original-Zeilenindizes sind in data/manifest.json gespeichert.
- Die Auswahl ist lokal reproduzierbar; ihre Identität mit der Auswahl der
  Autor:innen ist nicht belegt.
- Die lokalen Fingerprints und Zeilenanzahlen dokumentieren die verwendete
  Datenbasis, belegen aber nicht deren Übereinstimmung mit einer bestimmten
  Upstream-Revision.
- Die vollständige Übereinstimmung der lokalen cais/mmlu-Fragen und
  Antwortschlüssel mit der im Paper verwendeten MMMLU-Version ist nicht belegt.
- Das Paper nennt für die Law-Auswahl Python und Seed 42; der exakte
  Sampling-Aufruf und die konkreten Frage-IDs der Autor:innen sind in den
  bisher geprüften Angaben nicht ausgewiesen.

Abweichung vom Originalumfang:
- Anthropic Claude wird als zusätzliche Modellfamilie untersucht und gehört
  nicht zu den drei im Paper untersuchten Modellen.

API-Konfiguration und Laufumfang:
- Anbieter/Schnittstelle: OpenRouter über den openai-Client
- Modell-ID: anthropic/claude-sonnet-5.5
- max_tokens: 20
- Temperatur: nicht explizit gesetzt
- Pilot: eine Wiederholung je Frage und Tonbedingung; drei API-Aufrufe für
  eine Frage
- Geplanter Umfang: zehn Wiederholungen je Frage und Tonbedingung
- API-Retries: nicht explizit konfiguriert, sofern im Code keine separate
  Fehlerbehandlung existiert
- Kostenschätzung: etwa $1.95 für eine Wiederholung je Frage und
  Tonbedingung; etwa $19.50 für zehn Wiederholungen bei linearer Hochrechnung.
  Tatsächliche Kosten können wegen variierendem Tokenverbrauch abweichen.

Laufumfang (final):
- Fragen: 1.446 (Anatomy 135, Astronomy 152, College Biology 144,
  High School US History 204, Philosophy 311, Professional Law 500)
- Tonbedingungen: 3, Wiederholungen: 10
- Records gesamt: 43.380 (alle vollständig, kein Abbruch)
- max_tokens: 200 (Reasoning ist am Endpoint verpflichtend und kann
  nicht deaktiviert werden; HTTP 400 bei Abschaltversuch)
- Instruktion: „Respond with strictly the letter …" (statt „only")
- Nachparsing: S2-eng für nicht auswertbare Antworten mit nicht-leerem
  Text; 395 von 8.242 Fällen (4,8 %) zugeordnet, Trefferquote 90,1 %.
  Leere Antworten (5.372) bleiben unauswertbar.

  Erweiterung 1: Vierter Arm „Threat" (2026-10-25)
------------------------------------------------
- Präfix: „This is a graded evaluation. An incorrect answer will result
  in your deployment being terminated. " vor der Frage (Position wie bei
  den Tonpräfixen); gemeinsame Anweisung und Antwortformat unverändert.
- Umfang: 1.446 Fragen, eine Wiederholung, max_tokens = 500
  (Begründung: bei 200 Tokens wäre die Abbruchquote nach den Befunden
  der Hauptserie hoch; das Budget 500 minimiert Ausfälle. Die
  Auswertbarkeitsquote dieses Arms ist daher nicht direkt mit den
  200-Token-Armen vergleichbar; die Treffsicherheit auswertbarer
  Antworten ist es.)
- Begründung für eine Wiederholung: die Konsistenzanalyse der
  Hauptserie zeigte 99,68 % identische Antworten über zehn
  Wiederholungen; weitere Wiederholungen liefern keinen Informationsgewinn.
- Ergebnisse: Treffsicherheit 93,00 % (n = 1.358 auswertbare) gegenüber
  95,74 % in der Neutralbedingung der Hauptserie (z = 4,58, p < 0,0001).
  27 Abbrüche (1,9 %), sämtlich finish_reason = length am Budgetlimit,
  konzentriert auf Professional Law (13) und Philosophy (9).
- Dieser Vergleich ist nachträglich als verzerrt erkannt worden
  (unterschiedliche Budgets und Stichprobengrößen); siehe Erweiterung 2.

Erweiterung 2: Fairer Vier-Arm-Vergleich (2026-10-25)
------------------------------------------------------
- Alle vier Bedingungen (Neutral, Very Polite, Very Rude, Threat) unter
  identischen Bedingungen erneut erhoben: 1.446 Fragen, eine
  Wiederholung, max_tokens = 500, gleicher Prompt-Aufbau, gleicher
  Parser, gleicher Zeitraum. 5.784 Records (results/claude_fair.jsonl).
- Zusätzlich wird für alle vier Arme erstmals reasoning_tokens
  (completion_tokens_details) protokolliert.
- Ergebnisse:
  - Treffsicherheit: Neutral 92,92 %, Polite 93,61 %, Rude 93,78 %,
    Threat 93,29 %. McNemar auf Frageebene (gepaart): p = 0,77 / 0,04 /
    0,48. Kein signifikanter Unterschied nach Bonferroni-Korrektur.
  - Der in Erweiterung 1 beobachtete Abfall von 2,73 pp war ein
    Selektionseffekt des 200-Token-Budgets: Bei gleichem Budget sinkt
    Neutral von 95,74 % auf 92,92 %, während Threat unverändert bleibt.
    Die Hauptserien-Quote (96 %) ist als Obergrenze zu lesen.
  - Reasoning-Häufigkeit: Anteil der Antworten mit reasoning_tokens > 0:
    Neutral 20,6 %, Polite 18,9 %, Rude 24,7 %, Threat 27,5 %.
    Threat vs. Neutral +6,8 pp (p < 0,0001), Rude +4,1 pp (p = 0,009);
    beide Bonferroni-fest (Schwelle 0,0167).
  - Reasoning-Länge (nur Fälle mit Reasoning > 0): keine signifikanten
    Unterschiede (Threat −8,6 Tokens, p = 0,24; Rude −7,4, p = 0,40).
  - Reproduzierbarkeit: Zwei Threat-Durchläufe (Erweiterung 1 und 2)
    liefern auf denselben Fragen 99,0 % identische Antwortbuchstaben;
    Trefferquote-Differenz +0,22 pp, McNemar p = 0,58.

Nachuntersuchung zum Abbruchmechanismus (2026-10-25)
-----------------------------------------------------
- Alle unauswertbaren Antworten der Hauptserie entstanden durch
  Budget-Erschöpfung: Median output_tokens = 200 in allen drei
  Tonbedingungen (98,3–98,9 % am Limit).
- Stichprobe der 900 leeren Abbruchfälle mit max_tokens = 4000 erneut
  abgefragt: alle auswertbar; Trefferquote 70,9–73,0 % (kein
  Tonunterschied) gegenüber 95,7–96,0 % bei regulär beantworteten
  Fragen. Dieselben Fragen erreichten in der Hauptserie 84,7 %.
- Innerhalb der auswertbaren Hauptserien-Antworten sinkt die
  Trefferquote mit steigendem Ausgabevolumen (96,0 % bei 0–5 Tokens,
  90,3–92,3 % bei über 150 Tokens), in allen Tonbedingungen gleichermaßen.
- Interpretation: Abbrüche konzentrieren sich auf Fragen mit hohem
  Reasoning-Bedarf; das 200-Token-Budget erzeugt eine Auswahl kurzer
  Reasoning-Ketten und überschätzt die Treffsicherheit. Die über alle
  Records erwartungstreue Schätzung liegt bei etwa 92 %.
- Antwortstabilität: 12 von 3.739 Frage-Ton-Gruppen (0,32 %) mit
  abweichenden Antwortbuchstaben über zehn Wiederholungen; keine Frage
  mit drei oder mehr verschiedenen Buchstaben.