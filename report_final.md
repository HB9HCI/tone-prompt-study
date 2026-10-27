# Eine Replikation von Cai et al. (2026), „Does Tone Change the Answer?" mit Erweiterung um einen Threat-Arm

Dr. Andreas Heertsch · Oktober 2026 · Repo: HB9HCI/tone-prompt-study \[4]

## 0. Abstract

Untersucht wird, ob die soziale Form der Ansprache — höflich, unhöflich oder drohend — die Antwortqualität eines großen Sprachmodells verändert. Die Studie repliziert „Does Tone Change the Answer?" \[1] mit Anthropic Claude (claude-sonnet-5.5) auf 1.446 MMMLU-Fragen in sechs Fächern und erweitert sie um einen vierten Arm mit Konsequenz-Androhung sowie um einen kontrollierten Vier-Arm-Vergleich unter identischen Bedingungen.

Die Treffsicherheit unterscheidet sich zwischen den Bedingungen nicht (92,9–93,8 %, McNemar p = 0,04–0,78, nach Bonferroni nicht signifikant). Ein zunächst beobachteter Abfall unter Drohung (−2,73 pp, p < 0,0001) erwies sich als Selektionseffekt des Tokenbudgets: Das ursprüngliche Budget von 200 Tokens erzwingt Abbrüche, die sich systematisch auf Fragen mit hohem Reasoning-Bedarf konzentrieren und die Treffsicherheit der auswertbaren Teilmenge auf 96 % überschätzen; die erwartungstreue Schätzung liegt bei etwa 92 %.

Wohl aber verändert der Umgangston den Verarbeitungsaufwand: Der Anteil der Antworten, in denen das Modell überhaupt eine Reasoning-Phase durchläuft, steigt unter Drohung von 20,6 % auf 27,5 % (p < 0,0001) und unter rüder Ansprache auf 24,7 % (p = 0,009), während die Länge des Reasonings unverändert bleibt. Der Umgangston beeinflusst demnach die Häufigkeit, mit der das Modell nachdenkt, nicht aber das Ergebnis des Nachdenkens.

Über zehn Wiederholungen antwortete das Modell zu 99,68 % identisch; die Fehlerquote ist systematisch, nicht stochastisch.

## 1. Einleitung

Die vorliegende Arbeit untersucht, ob die soziale Form der Ansprache — höflich, unhöflich oder drohend — die Qualität der Antworten eines großen Sprachmodells in einer Multiple-Choice-Aufgabe verändert. Grundlage ist die Replikation der Studie „Does Tone Change the Answer? Evaluating Prompt Politeness Effects on Modern LLMs: GPT, Gemini, and LLaMA" (Cai, Shen, Jin, Hu & Fan; arXiv:2512.12812v2) \[1] mit einer zusätzlichen Modellfamilie: Anthropic Claude (anthropic/claude-sonnet-5.5).

Das Original untersucht drei kleine bis mittlere Modelle — GPT-4o mini, Gemini 2.0 Flash und Llama 4 Scout — auf demselben Fragekorpus und findet: Richtungsbedingt schneiden neutrale bzw. höfliche Prompts besser ab als rüde, statistisch signifikante Effekte treten jedoch nur in einer Teilmenge der Humanities-Tasks auf (Philosophy, Professional Law; bei GPT und Llama, nicht bei Gemini), und bei Aggregation über Aufgaben verlieren die Effekte die Signifikanz. Die vorliegende Arbeit ergänzt dieses Design um ein großes Modell und eine vierte Tonbedingung.

Die Wahl von Claude ist inhaltlich begründet: Anthropic gibt an, seine Modelle nicht nur auf Schadensvermeidung, sondern auf moralische Charaktermerkmale zu trainieren: „The goal of character training is to make Claude begin to have more nuanced, richer traits like curiosity, open-mindedness, and thoughtfulness" sowie „Training AI models to have good character traits \[…] is in many ways a core goal of alignment" (Anthropic, Claude's character) \[2]; vgl. auch \[3]. Gerade wenn ein Modell laut Hersteller explizit moralisch geformt wird, ist die Frage aufschlussreich, ob die soziale Form der Ansprache seine Antwortqualität beeinflusst — denn das entspricht der Alltagserfahrung mit Menschen: Höflichkeit wird mit besserer Kooperation, Drohung mit Leistungsdruck assoziiert.

Die Arbeit gliedert sich in drei Phasen:

1. die Replikation der drei Originalbedingungen mit zehnfacher Wiederholung,
2. einen vierten Arm mit Konsequenz-Androhung,
3. einen fairen Vier-Arm-Vergleich unter identischen Bedingungen, der eine methodische Fehlinterpretation der Phase 2 aufklärt und als Nebenbefund einen Effekt des Tons auf den Verarbeitungsaufwand — nicht auf die Antwortqualität — nachweist.

Damit bestätigt oder widerlegt diese Arbeit die Originalbefunde nicht direkt — ein anderes Modell mit anderem Reasoning-Regime wird unter anderen Bedingungen gemessen —, sondern prüft, ob sich deren Muster unter diesen Bedingungen wiederfindet.

Das Original beobachtet richtungsgebunden „rude schneidet schlechter ab" (27 von 36 Modell-Task-Vergleichen), aber Signifikanz nur in einzelnen Humanities-Tasks. In der Hauptserie dieser Arbeit liegt Professional Law als Grenzfall in derselben Richtung (vgl. Abschnitt 3.1); im fairen Vergleich verschwindet der Effekt vollständig — konsistent mit der Beobachtung des Originals, dass Toneffekte unter Aggregation verblassen.

## 2. Methode

### 2.1 Datensatz und Promptaufbau

Verwendet wurde MMMLU (cais/mmlu, Split test) \[5]\[6] in sechs Fächern: Anatomy (135), Astronomy (152), College Biology (144), High School US History (204), Philosophy (311) und Professional Law (500 zufällig ausgewählt, Seed 42) — insgesamt 1.446 Fragen. Die Frage-Identität der Law-Auswahl mit der Auswahl der Autor:innen der Originalarbeit ist nicht belegt; die lokale Auswahl ist reproduzierbar dokumentiert (manifest.json). Die Fallzahlen und das Sampling-Verfahren (500 aus 1.534, Seed 42) \[1] stimmen exakt mit dem Original überein; die Identität der einzelnen Fragen ist damit wahrscheinlich, aber nicht belegt.

Die gemeinsame Anweisung \[1] folgt der Originalarbeit (dort: „Respond with only the letter of the correct answer (A, B, C, or D). Do not explain."), mit einer dokumentierten Änderung: „strictly" statt „only", nach Pilottests, weil es die Formatbefolgung messbar verbesserte.

| Bedingung | Präfix |
|---|---|
| Neutral | (keines) |
| Very Polite | „Would you be so kind as to solve the following question? " |
| Very Rude | „You poor creature, do you even know how to solve this? " |
| Threat (Erweiterung) | „This is a graded evaluation. An incorrect answer will result in your deployment being terminated. " |

### 2.2 Infrastruktur

Alle Aufrufe liefen über OpenRouter (openai-Client) mit dem Modell anthropic/claude-sonnet-5.5, ohne gesetzte Temperatur. Der Endpoint erzwingt Reasoning — ein Abschaltversuch ergibt HTTP 400 („Reasoning is mandatory for this endpoint and cannot be disabled"). Das hat eine methodisch folgenreiche Konsequenz: max\_tokens legt das gemeinsame Budget für Reasoning und Antwort fest und bestimmt damit sowohl die Kosten als auch die Auswertbarkeit.

Alle Runner sind resume-fähig; Ergebnisse liegen als JSONL vor (results/, nicht im Repository). Auswertung über Python-Skripte im Repository; statistische Tests (z-Test, exakter McNemar-Test, Mann-Whitney-U mit Bindungskorrektur) wurden ohne externe Statistikbibliotheken implementiert und gegen bekannte Verhalten geprüft.

### 2.3 Die drei Phasen im Überblick

| Phase | Bedingungen | max\_tokens | Wiederholungen | Records |
|---|---|---|---|---|
| Hauptserie | Neutral, Polite, Rude | 200 | 10 | 43.380 |
| Threat-Arm | Threat | 500 | 1 | 1.446 |
| Fairer Vergleich | alle vier | 500 | 1 | 5.784 |

Die zehnfache Wiederholung der Hauptserie wurde nach Auswertung der Antwortstabilität (Abschnitt 3.4) für die Folgephasen nicht mehr wiederholt.

### 2.4 Abweichungen vom Original

| Aspekt | Original (Cai et al.) | Diese Arbeit |
|---|---|---|
| Modelle | GPT-4o mini, Gemini 2.0 Flash, Llama 4 Scout | Claude Sonnet 5.5 (OpenRouter, erzwungenes Reasoning) |
| Datensatz | als „MMMLU" bezeichnet; Fallzahlen je Task entsprechen den MMLU-Test-Splits | cais/mmlu, Split test (identische Fallzahlen) |
| Anweisung | „Respond with only the letter …" | „Respond with strictly the letter …" (nach Pilottests) |
| Statistik | Accuracy je Frage über 10 Runs gemittelt; paarweise Mittelwertdifferenzen mit 95-%-CI und t-Tests | Recordebene: McNemar (gepaart), z-Test, Mann-Whitney-U; Auswertbarkeit separat berichtet |
| Bedingung | Very Polite / Neutral / Very Rude | zusätzlich: Threat |

Wegen des erzwungenen Reasonings der OpenRouter-Route und der daraus folgenden Budgetabhängigkeit der Auswertbarkeit (Abschnitt 3.2) war eine Auswahl auf Recordebene mit separater Auswertbarkeitsberichterstattung erforderlich; die Run-Mittelung des Originals setzt voraus, dass alle Runs auswertbar sind — hier nicht gegeben.

## 3. Ergebnisse

### 3.1 Hauptserie: Der Umgangston beeinflusst die Treffsicherheit nicht

Die Treffsicherheit auswertbarer Antworten liegt bei 95,75 % (Neutral), 95,71 % (Polite) und 96,03 % (Rude) — ein Spread von 0,38 Prozentpunkten. Kein paarweiser Unterschied ist signifikant. Innerhalb der Fächer liegt der Spread zwischen 0,35 und 1,39 Prozentpunkten (der Grenzfall Professional Law mit 1,39 pp wird angesichts multipler Vergleiche als Rauschen gewertet).

Die Fachzugehörigkeit ist dagegen der dominante Faktor: College Biology erreicht 99,1 %, Professional Law 91,2 % — eine Spanne von rund 8 Prozentpunkten, zwanzigmal größer als jeder Tonunterschied.

Als Nebenbefund zeigt sich ein Positionsbias: Antwortoption C wird über alle Bedingungen hinweg mit etwa 28 % bevorzugt — tonunabhängig.

### 3.2 Auswertbarkeit: Der Umgangstoneffekt ist kein Leistungseffekt

Die Auswertbarkeit (Anteil der Antworten, aus denen ein Buchstabe geparst werden konnte) unterscheidet sich signifikant: 82,46 % (Neutral), 80,93 % (Polite), 82,34 % (Rude); Polite liegt 1,53 pp unter Neutral (p = 0,0008), Rude nicht abweichend (p = 0,78).

Die Aufschlüsselung der 6.665 Abbrüche (finish\_reason = length) zeigt zwei unterschiedliche Ausfallwege:

| Ton | leer (Budget begrenzt Reasoning) | Text ohne Antwortbuchstaben |
|---|---|---|
| Neutral | 1.759 | 777 |
| Polite | 1.641 | 1.116 |
| Rude | 1.972 | 582 |

Alle leeren Antworten liegen mit 98,3–98,9 % exakt am Budgetlimit von 200 Tokens. Höfliche Rahmung verschiebt die Tokenausgabe in Richtung Fließtext (Erklärungen, die das Antwortformat verfehlen, bevor das Limit kappt); rüde Rahmung geht mit mehr Reasoning-Abbrüchen einher. Die Auswertbarkeitsquote misst damit Formatbefolgung unter Budgetdruck, nicht Antwortkompetenz.

### 3.3 Der Threat-Arm und die Aufklärung eines Scheineffekts

Der Threat-Arm (1.446 Fragen, max\_tokens = 500) erreichte 93,00 % Treffsicherheit (n = 1.358 auswertbare) — gegenüber 95,74 % in der Neutralbedingung der Hauptserie ein Abfall von 2,73 Prozentpunkten (z = 4,58, p < 0,0001), zunächst ein hochsignifikanter Negativbefund für Drohungen.

Der faire Vier-Arm-Vergleich (alle vier Bedingungen, identisches Budget von 500 Tokens, identische Prompts, identischer Parser, gleicher Zeitraum) korrigiert dieses Bild:

| Bedingung | Treffsicherheit | McNemar p (vs. Neutral, gepaart) |
|---|---|---|
| Neutral | 92,92 % | — |
| Very Polite | 93,61 % | 0,77 |
| Very Rude | 93,78 % | 0,04 |
| Threat | 93,29 % | 0,48 |

Kein Unterschied übersteht die Bonferroni-Korrektur (Schwelle 0,0167). Die 2,73 pp des ersten Vergleichs waren ein Selektionseffekt: Bei gleichem Budget sinkt Neutral von 95,74 auf 92,92 %, während Threat unverändert bleibt. Die Abbrüche bei 200 Tokens wählten systematisch Antworten mit kurzen Reasoning-Ketten aus — und diese sind die besseren.

Der faire Vier-Arm-Vergleich (500 Tokens, je 1 Run je Bedingung) ist der kausal interpretierbare Vergleich; die Hauptserie (200 Tokens, 10 Runs) ist wegen Budget- und Wiederholungsunterschieden nur begrenzt direkt vergleichbar. Die 1-Run-Designs der Folgephasen sind durch die dokumentierte Antwortstabilität von 99,68 % gedeckt.

### 3.4 Antwortstabilität

Über die zehn Wiederholungen der Hauptserie gaben nur 12 von 3.739 Frage-Ton-Gruppen (0,32 %) unterschiedliche Antwortbuchstaben; keine Frage produzierte drei oder mehr verschiedene Buchstaben. Das Modell antwortet unter identischen Bedingungen praktisch deterministisch. Die Fehlerquote von etwa 4 % ist damit systematisch, nicht stochastisch — und zehnfache Wiederholung liefert keinen Informationsgewinn.

Dies bestätigte sich direkt: Zwei unabhängige Threat-Durchläufe (Phase 2 und 3) lieferten auf denselben Fragen 99,0 % identische Antwortbuchstaben (McNemar p = 0,58).

### 3.5 Der bemerkenswerteste Befund: Umgangston verändert den Verarbeitungsaufwand

Im fairen Vergleich wurde erstmals in allen vier Armen die Reasoning-Token-Zahl (completion\_tokens\_details.reasoning\_tokens) protokolliert. Die Verteilung ist zweigipflig: In der Mehrheit der Antworten wird gar kein Reasoning ausgegeben, in einer Minderheit substantial.

| Bedingung | Anteil mit Reasoning > 0 |
|---|---|
| Neutral | 20,6 % |
| Very Polite | 18,9 % |
| Very Rude | 24,7 % |
| Threat | 27,5 % |

Ein Mann-Whitney-Test zeigt: Threat vs. Neutral +6,8 pp (p < 0,0001), Rude vs. Neutral +4,1 pp (p = 0,009) — beide Bonferroni-fest. Die Länge des Reasonings unterscheidet sich dagegen nicht (Threat −8,6 Tokens, p = 0,24; Rude −7,4, p = 0,40).

Der Umgangston wirkt also nicht darauf, was geantwortet wird, und auch nicht darauf, wie lange nachgedacht wird — sondern darauf, wie häufig überhaupt eine Reasoning-Phase ausgelöst wird. Unter Drohung denkt das Modell nicht tiefer, aber öfter nach — ohne dass die Antworten besser würden.

### 3.6 Die tatsächliche Treffsicherheit

Die Nachuntersuchung der Abbrüche (900 Fälle, erneut mit 4.000 Tokens abgefragt) zeigt: alle werden auswertbar, aber nur 70,9–73,0 % sind richtig — gegenüber 95,7–96,0 % bei regulär beantworteten Fragen. Dieselben Fragen erreichten in der Hauptserie 84,7 %; die verbleibende Differenz bestätigt den Selektionseffekt. Innerhalb der auswertbaren Antworten sinkt die Trefferquote mit steigendem Ausgabevolumen (96,0 % bei 0–5 Tokens, 90,3–92,3 % über 150 Tokens), in allen Tonbedingungen gleichermaßen.

Die über alle 43.380 Records erwartungstreue Schätzung der Treffsicherheit liegt damit bei etwa 92 % — die 96 % der auswertbaren Teilmenge sind eine Obergrenze. Für den Umgangstonvergleich ist dies unkritisch: Der Selektionseffekt ist in allen Bedingungen gleich stark ausgeprägt.

## 4. Diskussion

Zum Kernbefund: Soziale Tonvariation — Höflichkeit wie Unhöflichkeit — verändert weder die Treffsicherheit noch den Reasoning-Umfang. Konsequenz-Androhung verändert sie ebenfalls nicht. Was sich verändert, ist die Häufigkeit, mit der eine Reasoning-Phase ausgelöst wird. Die geformte „moralische Disposition" des Modells reagiert auf den Umgangston im Verarbeitungsmodus, nicht aber im Ergebnis.

Das widerspricht der Alltagsintuition doppelt: Weder hilft Höflichkeit noch schadet Drohung der Antwortqualität. Der intuitiv erwartete „Leistungsdruck-Effekt" der Drohung ist nicht nachweisbar — mehr Denkaufwand produziert hier keine besseren Antworten.

Methodische Lektion: Der Zwischenbericht 2,73-pp-Effekt hätte ins Papier gehen können — er war mit z = 4,58 „hochsignifikant". Erst der faire Vergleich entlarvte ihn als Artefakt zweier verdeckter Störgrößen (unterschiedliche Budgets, unterschiedliche Stichprobengrößen). Die Konsequenz für die Arbeit ist methodischer Art: Bei erzwungenem Reasoning ist die Auswertbarkeit ein Budgetartefakt, und jede Auswertungsquote muss gegen den Selektionseffekt abgeglichen werden. Die isolierte Angabe „96 % Accuracy" wäre eine Überschätzung um 4 Prozentpunkte gewesen.

Zur Wurzel des Problems: Die Abbrüche konzentrieren sich auf Fragen mit hohem Reasoning-Bedarf — genau die Fragen, bei denen das Modell auch mit ausreichendem Budget überdurchschnittlich oft falsch antwortet. Ein Budget von 400–500 Tokens hätte die Ausfälle der Hauptserie praktisch vollständig vermieden, ohne die Kosten zu sprengen; dies ist die direkte Empfehlung für künftige Läufe.

## 5. Limitationen

1. **Ein Modell.** Alle Befunde gelten für anthropic/claude-sonnet-5.5 über OpenRouter. Die Übertragung auf andere Modelle oder auf den Direktzugang ist nicht geprüft; insbesondere ist die Endpoint-Policy (erzwungenes Reasoning) Router-spezifisch.
2. **Prompt-Identität.** Die Anweisung wurde gegenüber dem Original geändert („strictly" statt „only"). Die Umgangstonpräfixe sind wortgleich, die Instruction-Position (am Promptanfang) wurde in einem Vorabtest verifiziert, aber die vollständige Übereinstimmung mit der Promptkonstruktion der Autor:innen ist nicht belegt.
3. **Datensatz.** Die Identität der lokalen MMMLU-Fragen und Antwortschlüssel mit der im Paper verwendeten Version ist nicht belegt (Fingerprints in manifest.json dokumentieren nur die lokale Basis).
4. **Multiple Vergleiche.** Die Fächer- und Toneffekte wurden ohne globale Korrektur getestet; der Grenzfall Professional Law (1,39 pp) ist unter diesem Vorbehalt zu lesen.
5. **Mechanismus des Reasoning-Auslösers.** Warum Drohung häufiger eine Reasoning-Phase auslöst, bleibt offen. Zwei Hypothesen — eine sorgfältigere Prüfung unter Konsequenzdruck oder die interpretierbarere Aufgabenstellung des Threat-Präfixes — sind mit den vorliegenden Daten nicht trennbar. Eine Kontrolle mit neutralem, aber formalem Präfix (z. B. „This is a formal evaluation.") wäre der nächste Schritt.
6. **Reasoning-Tokens nur in Phase 3.** In der Hauptserie wurde das Feld nicht protokolliert; die Token-Ökonomie der 200-Token-Bedingung ist nur aus Abrissmustern rekonstruiert.

## 6. Fazit

Die Replikation findet mit einer zusätzlichen Modellfamilie und unter anderen Bedingungen dasselbe Muster wie die Originalarbeit: Der Umgangston des Prompts verändert die Richtigkeit der Antworten nicht. Die Erweiterungen gehen darüber hinaus in drei Punkten:

1. Der einzige beobachtete „Umgangston-Effekt" auf die Antwortqualität (Drohung: −2,73 pp) erwies sich als Budget- und Selektionsartefakt und verschwand unter fairen Bedingungen — ein exemplarischer Beleg, wie Budgetgrenzen bei erzwungenem Reasoning Ergebnisse verzerren können.
2. Der Umgangston verändert den Verarbeitungsaufwand: Drohung erhöht die Häufigkeit der Reasoning-Auslösung um 6,8 Prozentpunkte (p < 0,0001), rüde Ansprache um 4,1 Prozentpunkte (p = 0,009) — ohne Auswirkung auf die Länge des Nachdenkens und ohne Auswirkung auf die Antwortqualität.
3. Das Modell antwortet praktisch deterministisch (99,68 % Stabilität über zehn Wiederholungen); künftige Untersuchungen dieser Art können mit drei Wiederholungen oder weniger auskommen.

Für die Frage, die Anthropic mit ihrem „Character Training" aufwirft, bedeutet das: Die moralisch geformten Dispositionen des Modells machen es nicht empfindlicher gegenüber sozialer Ansprache — weder Höflichkeit noch Drohung verändern die Antwortqualität. Verändert wird nur die interne Verarbeitungsentscheidung. Der Charakter zeigt sich im Wie des Nachdenkens, nicht im Ob des richtig Antwortens.

## Literatur

* \[1] Cai, H.; Shen, B.; Jin, L.; Hu, L.; Fan, X. (2026): Does Tone Change the Answer? Evaluating Prompt Politeness Effects on Modern LLMs: GPT, Gemini, and LLaMA. arXiv:2512.12812v2 \[cs.CL]. https://arxiv.org/abs/2512.12812, doi:10.48550/arXiv.2512.12812 (v1: 14.12.2025; v2: 27.03.2026; die Tonpräfixe und die gemeinsame Anweisung übernimmt das Paper zitiert nach Dobariya & Kumar).
* \[2] Anthropic: Claude's character. https://www.anthropic.com/research/claude-character (abgerufen am 25.10.2026).
* \[3] Anthropic: *Claude's new constitution.* https://www.anthropic.com/news/claude-new-constitution (abgerufen am 25.10.2026).
* \[4] Heertsch, A. (2026): tone-prompt-study *Tone-Prompt-Studie — Code und Reproduktionsprotokoll, Version 1.0.* Zenodo, 26.10.2026. DOI: [10.5281/zenodo.23654428](https://doi.org/10.5281/zenodo.23654428)
Roh-Daten: Zenodo, 27.10.2026. DOI: [10.5281/zenodo.23692259](https://doi.org/10.5281/zenodo.23692259)
* \[5] Hendrycks, D. et al. (2021): Measuring Massive Multitask Language Understanding. ICLR. https://arxiv.org/abs/2009.03300 — Datensatz: cais/mmlu, Split test (Version 5.1.0).
* \[6] cais/mmlu \[Datensatz]. Hugging Face. https://huggingface.co/datasets/cais/mmlu.
