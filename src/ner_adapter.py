"""Adapter: HF token-classification output -> evaluation schema."""
import re
from sectionizer import split_sections
from rules_extractor import (LEXICON, DOSE_RE, ROUTE_RE, FREQ_RE, NEG_CUES, PAST_CUES,
                             SECTION_STATUS, SKIP_SECTIONS, FREQ_CANON, ROUTE_CANON,
                             segment_medication_list, _canon)

DRUG_LABELS = {"medication", "drug", "chemical", "medicine"}


def normalize_drug(surface):
    s = surface.lower().strip()
    if s in LEXICON:
        return LEXICON[s]["generic"], LEXICON[s]["is_brand"], True
    for term, info in LEXICON.items():
        if re.search(r"\b" + re.escape(term) + r"\b", s):
            return info["generic"], info["is_brand"], True
    return s, False, False


def ner_to_records(note, entities, note_id=None, min_score=0.5):
    sections = split_sections(note)
    bounds, cursor = [], 0
    for sec, body in sections.items():
        idx = note.find(body, cursor) if body else -1
        if idx >= 0:
            bounds.append((idx, idx + len(body), sec))
            cursor = idx + len(body)

    def section_at(pos):
        for s, e, sec in bounds:
            if s <= pos < e:
                return sec
        return "_unsectioned"

    out = []
    for ent in entities:
        if ent["entity_group"].lower() not in DRUG_LABELS or ent["score"] < min_score:
            continue
        sec = section_at(ent["start"])
        if sec in SKIP_SECTIONS or sec.startswith("exam:"):
            continue
        surface = note[ent["start"]:ent["end"]]
        generic, is_brand, in_lex = normalize_drug(surface)
        seg = next((s for _, s in segment_medication_list(sections.get(sec, note))
                    if surface.lower() in s.lower()), None)
        seg = seg or note[max(0, ent["start"] - 60): ent["end"] + 80]
        dose, route, freq = DOSE_RE.search(seg), ROUTE_RE.search(seg), FREQ_RE.search(seg)
        status = "allergy" if sec == "allergies" else SECTION_STATUS.get(sec, "mentioned")
        if sec != "allergies":
            if NEG_CUES.search(seg):
                status = "negated"
            elif PAST_CUES.search(seg):
                status = "historical"
        out.append({
            "note_id": note_id, "drug_text": surface, "normalized": generic,
            "is_brand": is_brand, "in_lexicon": in_lex,
            "dose": dose.group(0).strip() if dose else None,
            "route": _canon(route, ROUTE_CANON) if route else None,
            "frequency": _canon(freq, FREQ_CANON) if freq else None,
            "section": sec, "status": status, "score": round(ent["score"], 3),
        })
    seen, ded = set(), []
    for r in out:
        k = (r["note_id"], r["normalized"], r["section"], r["status"])
        if k not in seen:
            seen.add(k)
            ded.append(r)
    return ded
