"""Gradio demo: rules-only medication extraction on public sample notes.

Runs on CPU with no model downloads. This is the public-safe path from the
hybrid architecture — the transformer and LLM lanes are deliberately not
loaded here (see docs/ADR-001-hybrid-architecture.md and the model card).

This file lives in app/ alongside synced copies of sectionizer.py and
rules_extractor.py so the Hugging Face Space bundle is self-contained.
Regenerate the copies with: python scripts/sync_app.py
"""
import os

import pandas as pd
import gradio as gr

from rules_extractor import extract_medications


COLUMNS = ["drug_text", "normalized", "dose", "route", "frequency", "section", "status"]
COLUMN_LABELS = {
    "drug_text": "drug as written",
    "normalized": "normalized",
    "dose": "dose",
    "route": "route",
    "frequency": "frequency",
    "section": "section",
    "status": "status",
}


EXAMPLE_MEDS_LIST = """CHIEF COMPLAINT:,  Follow-up hypertension and hyperlipidemia.,ALLERGIES:,  PENICILLIN - causes rash.,CURRENT MEDICATIONS:,  1.  Lisinopril 20 mg p.o. daily.,2.  Lipitor 40 mg p.o. at bedtime.,3.  Metformin 1000 mg p.o. b.i.d.,4.  Aspirin 81 mg p.o. daily.,5.  Metoprolol 50 mg p.o. b.i.d.,PAST MEDICAL HISTORY:,  Hypertension, type 2 diabetes, hyperlipidemia.,ASSESSMENT AND PLAN:,  Stable. Continue current regimen. Recheck labs in 3 months."""

EXAMPLE_NARRATIVE = """CHIEF COMPLAINT:,  Chest pain.,HISTORY OF PRESENT ILLNESS:,  The patient is a 62-year-old male with a history of coronary artery disease who presents with substernal chest pain that began this morning. He took two sublingual nitroglycerin tablets at home with partial relief. He was previously on Plavix but discontinued it six months ago due to bruising. He denies taking any aspirin today. In the emergency department he was given morphine 4 mg IV for pain control and started on a heparin drip.,PAST MEDICAL HISTORY:,  CAD status post stent 2019, hypertension.,ASSESSMENT:,  Acute coronary syndrome, rule out MI. Admit to telemetry, cardiology consult."""

EXAMPLE_DISCHARGE = """HOSPITAL COURSE:,  The patient was admitted with community-acquired pneumonia and treated with IV antibiotics with good clinical response.,DISCHARGE DIAGNOSIS:,  Community-acquired pneumonia.,DISCHARGE MEDICATIONS:,  1.  Azithromycin 250 mg p.o. daily for 3 more days.,2.  Prednisone 20 mg p.o. daily, taper over 7 days.,3.  Albuterol inhaler 2 puffs q.i.d. as needed.,4.  Omeprazole 20 mg p.o. daily.,5.  Resume home Lisinopril 10 mg p.o. daily.,DISCHARGE INSTRUCTIONS:,  Follow up with primary care in 1 week. Return for worsening shortness of breath or fever."""


def extract(note: str) -> pd.DataFrame:
    if not note or not note.strip():
        return pd.DataFrame(columns=[COLUMN_LABELS[c] for c in COLUMNS])
    rows = extract_medications(note)
    if not rows:
        return pd.DataFrame(columns=[COLUMN_LABELS[c] for c in COLUMNS])
    df = pd.DataFrame(rows)
    for c in COLUMNS:
        if c not in df.columns:
            df[c] = None
    df = df[COLUMNS].rename(columns=COLUMN_LABELS)
    return df


HEADER_MD = """# Clinical Medication Extraction — public demo

Extracts medication events (drug, dose, frequency, route, clinical status) from
free-text clinical notes using a **rules + lexicon** pipeline (regex-based
sectionizer + brand/generic lexicon + negation/temporal cues).

This is the public-safe path of a larger hybrid system. The transformer NER and
local-LLM lanes are described in the repo but are **not loaded here** — this
Space runs on CPU only with no model downloads.

> ⚠️ **Not for clinical use.** Runs on public MTSamples-style sample notes.
> Never paste PHI or any patient-identifiable text into this demo.
"""

COMPARISON_MD = """## Four-way system comparison

Precision, recall, and F1 measured against a 75-note hand-annotated gold set.
Numbers are copied from `working/final_comparison.csv` (see notebook 08).

| system      | drug P | drug R | drug F1 | drug+status F1 | n predictions |
|-------------|-------:|-------:|--------:|---------------:|--------------:|
| rules       |  0.735 |  0.598 |   0.660 |          0.392 |           215 |
| transformer |  0.124 |  0.121 |   0.122 |          0.069 |           259 |
| llm         |  0.310 |  0.318 |   0.314 |          0.284 |           271 |
| **hybrid**  |  0.402 |  0.481 |   0.438 |      **0.403** |           316 |

**How to read this.** The rules lane wins on precision — it cannot hallucinate,
and its dose/route/frequency parsing is exact. The hybrid wins on `drug+status`
F1 because the LLM lane recovers narrative mentions (negations, historical use,
planned starts) that the lexicon-bound rules miss. The transformer lane on its
own does not normalize or assign status, so it is used inside the hybrid as a
lexicon-gap detector rather than a standalone extractor.

The full rationale — including the routing decision, cost/quality tradeoffs,
and revisit criteria — is in `docs/ADR-001-hybrid-architecture.md`.
"""


with gr.Blocks(title="Clinical Medication Extraction") as demo:
    gr.Markdown(HEADER_MD)

    with gr.Tabs():
        with gr.Tab("Extract"):
            with gr.Row():
                with gr.Column():
                    note_in = gr.Textbox(
                        label="Clinical note",
                        placeholder="Paste a public sample clinical note here…",
                        lines=16,
                    )
                    with gr.Row():
                        ex1 = gr.Button("Load example 1 — meds list + allergy")
                        ex2 = gr.Button("Load example 2 — narrative mentions")
                        ex3 = gr.Button("Load example 3 — discharge medications")
                    run_btn = gr.Button("Extract medications", variant="primary")
                with gr.Column():
                    table_out = gr.Dataframe(
                        headers=[COLUMN_LABELS[c] for c in COLUMNS],
                        label="Extracted medication events",
                        wrap=True,
                    )

            ex1.click(lambda: EXAMPLE_MEDS_LIST, outputs=note_in)
            ex2.click(lambda: EXAMPLE_NARRATIVE, outputs=note_in)
            ex3.click(lambda: EXAMPLE_DISCHARGE, outputs=note_in)
            run_btn.click(extract, inputs=note_in, outputs=table_out)
            note_in.submit(extract, inputs=note_in, outputs=table_out)

        with gr.Tab("Benchmark"):
            gr.Markdown(COMPARISON_MD)


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
    )
