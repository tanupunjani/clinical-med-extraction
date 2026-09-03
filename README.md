# Clinical Medication Extraction

Extracts medication events (drug, dose, frequency, route, clinical status) from
free-text clinical notes. Hybrid architecture: rules + local LLM, routed by
section type. See `CLAUDE.md` for the module map and `docs/ADR-001-hybrid-architecture.md`
for the routing rationale.

## Repo layout

- `src/` — the real modules (sectionizer, rules extractor, NER adapter, RAG
  normalizer, LLM extractor, evaluation harness). Notebooks import from here.
- `notebooks/` — the 8-notebook build sequence (`01_eda` → `08_hybrid_and_final`).
- `docs/` — ADR, model card, roadmap.
- `app/` — **deployment bundle for Hugging Face Spaces** (see below).
- `scripts/` — utility scripts.

Data directories (`data/`, `working/`, `gold/`) are gitignored. No PHI or
DUA-restricted data may ever be committed or sent to external APIs.

## `app/` — Hugging Face Space deployment bundle

`app/` is a **self-contained, flat deployment bundle**. Hugging Face Spaces
uploads the folder as-is with no parent directory, so `app.py` uses plain
sibling imports and the modules it depends on live next to it as copies.

The copies are generated — do **not** edit them directly. Edit the originals in
`src/` and re-run the sync script:

```bash
python scripts/sync_app.py
```

This copies `src/sectionizer.py` and `src/rules_extractor.py` into `app/` with
a "generated file" header. **Run it before every push to the Space**, or the
deployment will drift from source.

The Space runs the **rules + lexicon path only** — no transformer, no LLM, no
GPU, no model downloads. It fits on the free CPU tier and starts in a few
seconds. Public deployments never load the LLM lane; that is an architectural
constraint from the model card, not a configuration.

### Deploy

1. New Space on Hugging Face → Gradio SDK → CPU basic → Public.
2. Clone the Space repo locally.
3. Copy everything from `app/` (contents, not the folder itself) into the clone.
4. `git push` the clone.
