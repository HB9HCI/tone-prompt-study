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

