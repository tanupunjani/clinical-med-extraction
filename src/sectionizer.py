"""Sectionizer for flat (newline-free) clinical transcription notes."""
import re

HEADER_RE = re.compile(r"(?:^|[,.;:]\s*)([A-Z][A-Z0-9 /&()'-]{1,60}?)\s*:\s*,?\s*")
STOPWORDS = {'MD', 'AM', 'PM', 'RN', 'DR', 'NOTE', 'ADDENDUM'}
SECTION_MAP = {'HISTORY OF PRESENT ILLNESS': 'hpi', 'HISTORY OF THE PRESENT ILLNESS': 'hpi', 'HPI': 'hpi', 'INTERIM HISTORY': 'hpi', 'SUBJECTIVE': 'hpi', 'CHIEF COMPLAINT': 'chief_complaint', 'CC': 'chief_complaint', 'REASON FOR VISIT': 'chief_complaint', 'REASON FOR RETURN VISIT': 'chief_complaint', 'PAST MEDICAL HISTORY': 'pmh', 'PAST MEDICAL HISTORY/SURGERIES/HOSPITALIZATIONS': 'pmh', 'PMH': 'pmh', 'PAST SURGICAL HISTORY': 'psh', 'MEDICATIONS': 'medications', 'CURRENT MEDICATIONS': 'medications', 'MEDICATIONS ON ADMISSION': 'medications', 'HOME MEDICATIONS': 'medications', 'OTHER MEDICATIONS': 'medications', 'DIABETES MEDICATIONS': 'medications', 'DISCHARGE MEDICATIONS': 'discharge_medications', 'MEDICATIONS AT DISCHARGE': 'discharge_medications', 'ALLERGIES': 'allergies', 'DRUG INTOLERANCE': 'allergies', 'FAMILY HISTORY': 'family_history', 'SOCIAL HISTORY': 'social_history', 'REVIEW OF SYSTEMS': 'ros', 'ROS': 'ros', 'PHYSICAL EXAMINATION': 'physical_exam', 'PHYSICAL EXAM': 'physical_exam', 'OBJECTIVE': 'physical_exam', 'VITAL SIGNS': 'vitals', 'VITALS': 'vitals', 'LABORATORY DATA': 'labs', 'LAB STUDIES': 'labs', 'LABORATORY': 'labs', 'PERTINENT LABORATORIES': 'labs', 'ASSESSMENT': 'assessment', 'IMPRESSION': 'assessment', 'ASSESSMENT AND PLAN': 'assessment_plan', 'ASSESSMENT & PLAN': 'assessment_plan', 'PLAN': 'plan', 'TREATMENT PLAN': 'plan', 'RECOMMENDATIONS': 'plan', 'HOSPITAL COURSE': 'hospital_course', 'DISCHARGE DIAGNOSIS': 'discharge_diagnosis', 'DISCHARGE DIAGNOSES': 'discharge_diagnosis', 'PRINCIPAL DIAGNOSES': 'discharge_diagnosis', 'DISCHARGE INSTRUCTIONS': 'discharge_instructions', 'DISPOSITION': 'disposition', 'FOLLOWUP': 'followup', 'FOLLOW-UP': 'followup'}
EXAM_SUBHEADS = {'NECK', 'BREASTS', 'CARDIOVASCULAR', 'NEUROLOGIC', 'AXILLA', 'GI', 'GASTROINTESTINAL', 'GU', 'ORAL CAVITY', 'LYMPHATIC', 'PELVIS', 'SOCIAL', 'EYES', 'HEENT', 'PSYCHIATRIC', 'LUNGS', 'EXTREMITIES', 'BACK', 'HEART', 'ABDOMEN', 'THROAT', 'GENERAL', 'GENITOURINARY', 'MUSCULOSKELETAL', 'SKIN', 'PSYCHE', 'CHEST', 'NOSE', 'PSYCH', 'NEUROLOGICAL', 'RESPIRATORY', 'RECTAL'}


def _is_header(cand):
    c = cand.strip()
    if len(c) < 2 or len(c) > 60 or c in STOPWORDS:
        return False
    letters = [ch for ch in c if ch.isalpha()]
    if not letters:
        return False
    if sum(ch.isupper() for ch in letters) / len(letters) < 0.9:
        return False
    if re.fullmatch(r"[0-9 /.-]+", c):
        return False
    return True


def normalize_header(raw):
    if raw in SECTION_MAP:
        return SECTION_MAP[raw]
    if raw in EXAM_SUBHEADS:
        return "exam:" + raw.lower().replace(" ", "_")
    return raw.lower().replace(" ", "_").replace("/", "_")


def split_sections(note, normalize=True):
    if not isinstance(note, str) or not note.strip():
        return {}
    matches = [m for m in HEADER_RE.finditer(note) if _is_header(m.group(1))]
    if not matches:
        return {"_unsectioned": note.strip()}
    sections = {}
    if matches[0].start() > 0:
        pre = note[:matches[0].start()].strip(" ,.")
        if pre:
            sections["_preamble"] = pre
    for i, m in enumerate(matches):
        raw = m.group(1).strip()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(note)
        body = note[m.end():end].strip().strip(",").strip()
        key = normalize_header(raw) if normalize else raw
        sections[key] = sections[key] + " " + body if key in sections else body
    return sections


def coverage(note, sections):
    if not note:
        return 0.0
    return min(1.0, sum(len(v) for v in sections.values()) / len(note))
