# Model Card: Clinical Medication Extraction

**Version:** 1.0  |  **Date:** 2026-09-03

## Intended use
Extraction of medication events (drug, dose, frequency, clinical status) from
free-text clinical notes, for research and development purposes.

**In scope:** methods development, benchmarking, retrospective research cohorts.

**Out of scope — not validated for these:** clinical decision support, medication
reconciliation without human review, any use where output is acted on without a
clinician verifying it against the source note.

## Data
- Developed on MTSamples: 373 transcription samples, publicly available.
- These are teaching transcriptions, NOT EHR exports. They lack copy-forward
  text, EHR templating artifacts, and embedded lab tables.
- Evaluation: 75-note gold set, single annotator, guidelines v1 frozen before
  annotation. Intra-annotator agreement measured on 15 notes.
- No PHI was used at any stage. Public demo runs on open data only.

## Performance
See `final_comparison.csv`. Reported at two strictness levels (drug, drug+status)
with precision and recall separated. Metrics carry the ceiling imposed by
single-annotator agreement — see the gold set documentation.

## Known limitations and failure modes
1. **Negation scope** — simplified NegEx in the rules lane; cues are segment-scoped,
   not syntactically scoped. Known false positives (e.g. "switched to X without
   difficulty").
2. **Lexicon coverage** — drugs absent from RxNorm or below the similarity
   threshold return `needs_review` rather than a mapping.
3. **Formulation detail** — extended-release and combination formulations may
   normalize to the base ingredient.
4. **Hallucination** — the narrative lane uses a generative model. A faithfulness
   check flags extracted drugs absent from the source, but the check is itself
   imperfect (prefix matching tolerates near-misses).
5. **Domain shift** — performance on real EHR notes is unvalidated. MTSamples is
   cleaner and shorter than MIMIC discharge summaries.
6. **Section dependence** — routing relies on the sectionizer; headerless notes
   (~2% of the corpus) route entirely to the narrative lane.

## Privacy and governance
- All inference runs locally. No note content is sent to external APIs.
- This is an architectural constraint, not a configuration option: PHIPA and
  MIMIC's DUA both prohibit third-party transmission of clinical text.
- Quantized (4-bit) local models are used; quantization has a measurable quality
  cost and is a deployment tradeoff, not a free optimization.
- The public demo contains no restricted data and is fed only open-licensed
  or synthetic notes.

## Human oversight
Outputs are decision support at most. Low-confidence normalizations are flagged
`needs_review`; multi-drug segments withhold attributes rather than guess. The
system is designed to abstain rather than assert when uncertain.

## Contact
Maintainer: (your name). Issues: (repo URL).
