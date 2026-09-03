# Roadmap and deliberate exclusions
_Last updated 2026-09-03_

## Deferred, with the evidence that would change the decision

| Deferred | Why | Revisit when |
|---|---|---|
| Fine-tuning a clinical NER model | 373 notes; too small to train on, and pretrained + rules already covers the easy majority | MIMIC access gives 10k+ notes AND hybrid recall proves insufficient |
| Full NegEx/ConText | Simplified version affects ~3.5% of rules output; LLM lane handles the hard cases | Narrative-lane routing is removed, or negation errors exceed 5% |
| Span-level gold annotations | Event-level matching fits the task; span gold would cost another annotation pass | A clean detection-only comparison becomes necessary |
| Vector database (Chroma/FAISS) | ~10^5 concepts fit in a NumPy matrix; a DB adds ops burden for no gain | Vocabulary exceeds ~10^6 vectors or needs persistence + filtering |
| FHIR-formatted output | No consumer for it yet | An integration target exists |
| Multi-annotator gold set | Single annotator is the documented limitation; intra-annotator agreement bounds the metrics | The project moves toward anything clinical-facing |
| Kubernetes / autoscaling | Azure Container Apps handles this scale | Sustained load requires horizontal scaling |

## Next
1. Deploy: Gradio Space (demo), then FastAPI + Docker + Azure Container Apps
2. CI: lint, tests, eval-on-synthetic gate
3. MIMIC transfer: re-annotate 50 notes, rerun the comparison, write the
   generalization-gap analysis
