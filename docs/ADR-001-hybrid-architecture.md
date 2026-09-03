# ADR-001: Hybrid rules + LLM architecture for medication extraction

**Status:** Accepted
**Date:** 2026-09-03

## Context
Medication extraction from clinical notes, developed on MTSamples (373 notes),
evaluated against a 75-note hand-annotated gold set. Target environment is a
PHIPA-governed hospital: no external LLM APIs, outputs must be auditable.

Three detection approaches were built and measured against the same harness:
rules (lexicon + regex), transformer NER (d4data/biomedical-ner-all), and a
local instruct LLM (Qwen2.5-7B, 4-bit).

## Decision
Route by section type. Structured sections (medications, discharge medications,
allergies) are processed by the rules extractor; narrative sections (HPI,
hospital course, plan) by the LLM. Predictions are merged with rules winning
ties. RAG over RxNorm normalizes surface forms, abstaining below a similarity
threshold.

## Rationale
- Rules are precise, millisecond-fast, and cannot hallucinate by construction.
  Medication lists are the highest-stakes output and rules solve them.
- The LLM's measured advantage is confined to narrative prose: negation scope,
  temporal context, and multi-drug attribution.
- Routing sends roughly 99% of text to the expensive lane,
  cutting LLM cost proportionally versus an all-LLM design.
- Every prediction carries a `source` field, so any output is attributable.

## Consequences
Positive: hallucination exposure confined to the narrative lane; the medication
list itself is produced by auditable code; cost scales with narrative volume.

Negative: two components to maintain; routing depends on the sectionizer, so
sectionizer failures propagate; headerless notes fall entirely to the LLM lane.

## Alternatives considered
- **All-rules:** rejected — lexicon-bound recall, crude negation scope.
- **All-LLM:** rejected — cost, hallucination exposure on the medication list,
  and no auditable path for the highest-stakes output.
- **Transformer-only:** rejected — no normalization or status; strictly a
  detection component, better used as a lexicon-gap detector.
- **Fine-tuning:** deferred — 373 notes is too small; revisit with MIMIC access
  and only if hybrid recall proves insufficient.

## Revisit if
- MIMIC evaluation shows the sectionizer failing on real EHR formatting
- Narrative-lane precision within the hybrid falls below the rules lane
- A clinical use case requires sub-second latency end to end
