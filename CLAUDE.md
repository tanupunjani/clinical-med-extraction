# CLAUDE.md — clinical-med-extraction

## What this project does
Extracts medication events (drug, dose, frequency, route, clinical status) from
free-text clinical notes. Developed on MTSamples (373 notes), evaluated against a
75-note hand-annotated gold set. Architecture: section-based routing — structured
sections (medications, allergies) go to the rules extractor; narrative sections
(HPI, hospital course, plan) go to a local LLM (Qwen2.5-7B 4-bit). Predictions
are merged with rules winning ties. A RAG layer over RxNorm normalizes surface
forms via sentence-embedding similarity.

## Hard constraints — data privacy

**No PHI or DUA-restricted data may ever be committed or sent to external APIs.**

- `data/`, `working/`, `gold/`, and `*.parquet`/`*.csv` are gitignored for this reason.
- All inference runs locally. Sending note text to any third-party LLM API violates
  both PHIPA and the MIMIC DUA — this is an architectural constraint, not a setting.
- Public deployments (Gradio Space, HuggingFace) run the **rules + RAG path only**,
  with open-licensed or synthetic demo notes baked in. The LLM lane is never exposed
  publicly. Do not change this without explicit instruction.

## Module layout — src/

| File | Responsibility |
|---|---|
| `sectionizer.py` | Regex-based section splitter; maps raw headers → canonical keys |
| `rules_extractor.py` | Lexicon + regex extraction; brand→generic, dose/route/freq, negation |
| `ner_adapter.py` | Wraps HuggingFace token-classification output into evaluation schema |
| `llm_extractor.py` | Parses, validates, and faithfulness-checks LLM JSON output |
| `rag_normalizer.py` | Cosine-similarity normalization over an RxNorm embedding matrix |
| `evaluation.py` | Precision/recall/F1 harness at `drug` and `drug+status` levels |

## Notebook sequence — notebooks/

`01` EDA → `02` sectionizer → `03` rules → `04` gold & eval harness →
`05` transformer NER → `06` LLM extractor → `07` RAG normalization →
`08` hybrid system & final evaluation (ADR, model card, roadmap)

## Key docs
- `docs/ADR-001-hybrid-architecture.md` — routing decision and rationale
- `docs/MODEL_CARD.md` — intended use, limitations, privacy/governance
- `docs/ROADMAP.md` — deliberate exclusions and revisit criteria
