# tone-prompt-study

Does prompt tone change how a large language model answers multiple-choice
questions? This repository replicates the study *"Does Tone Change the
Answer?"* (version 2) with an additional model family — Anthropic Claude —
and extends it with a fourth prompt condition (*Threat*) and a controlled
follow-up under equal budgets.

## Design

- **Dataset:** MMMLU (cais/mmlu, split *test*), six subjects, 1,446 questions
  (Professional Law: 500 randomly sampled, seed 42)
- **Prompt conditions:** Neutral, Very Polite, Very Rude (replication)
  and Threat (extension)
- **Model:** `anthropic/claude-sonnet-5.5` via OpenRouter (openai client)
- **Response format:** strictly the letter A–D, no explanation

Three phases are documented:

| Phase | Conditions | max_tokens | Repetitions | Records |
|---|---|---|---|---|
| Main series | 3 tones | 200 | 10 | 43,380 |
| Threat arm | 4th condition | 500 | 1 | 1,446 |
| Fair comparison | all 4 | 500 | 1 | 5,784 |

The authoritative documentation of scope, deviations from the original
study, and all methodological decisions is **[protocol.md](protocol.md)**.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file with your OpenRouter API key:

```
OPENROUTER_API_KEY=***
```

## Reproduction

```powershell
# 1. Prepare the benchmark file
python prepare_data.py

# 2. Main series (43,380 calls, resumable)
python run_full.py

# 3. Evaluation
python evaluate_run.py            # overall + per subject
python evaluate_variants.py       # strict vs. reparsed answers
python ton_pro_fach.py            # tone effects within subjects
python konsistenz.py              # answer stability across repetitions
python finish_reason_check.py     # why answers were unparseable

# 4. Threat arm (1,446 calls)
python run_threat.py

# 5. Fair four-arm comparison under identical conditions (5,784 calls)
python run_fair.py
python evaluate_fair.py           # paired McNemar, budget effect, reasoning
python mw_test.py                 # Mann-Whitney tests on reasoning tokens
```

All runner scripts are **resumable**: on restart, successfully answered
items are skipped.

## Repository layout

| Path | Purpose |
|---|---|
| `protocol.md` | Full study protocol: scope, deviations, phases, findings |
| `data/` | `benchmark.jsonl` (1,446 items) and `manifest.json` (dataset fingerprints) |
| `results/` | Run outputs (JSONL), not committed |
| `prompts.py` | Prompt construction (tone prefixes, instruction) |
| `run_*.py` | Data collection runners |
| `evaluate_*.py`, `mw_test.py` | Analysis and statistics |
| `compare_runs.py`, `list_unparsed.py`, `reparse_strict.py` | Diagnostics |

## Notes

- The endpoint enforces reasoning (cannot be disabled); `max_tokens`
  therefore determines both cost and parseability. See `protocol.md`
  for the budget analysis.
- Results and their interpretation are documented in `protocol.md` and
  the accompanying report, not in this README.
- The sampling identity of the Professional Law subset with the original
  authors' selection is **not** established; see `protocol.md` for details.

## Status

Data collection and analysis are complete. The study report
(`report.md`) and the full pipeline are archived via Zenodo 

[![DOI](https://zenodo.org/badge/1426650025.svg)](https://doi.org/10.5281/zenodo.23654428)

Questions and issues via the issue tracker.


## Raw Data

The raw data you find here:

[![DOI](https://zenodo.org/badge/1426650025.svg)](https://doi.org/10.5281/zenodo.23692259)



