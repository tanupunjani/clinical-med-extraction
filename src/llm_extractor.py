"""Local LLM extraction: parsing, validation, faithfulness."""
import json, re

REQUIRED = {"drug", "dose", "frequency", "status"}
VALID_STATUS = {"active","discharge","allergy","historical","planned",
                "negated","inpatient","mentioned"}


def parse_llm_json(raw):
    if raw is None:
        return None, "empty"
    text = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    text = re.sub(r"\s*```$", "", text).strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("["), text.rfind("]")
        if start == -1 or end == -1 or end < start:
            return None, "no_array_found"
        try:
            obj = json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            return None, "malformed_json"
    if isinstance(obj, dict):
        for k in ("medications", "drugs", "results"):
            if isinstance(obj.get(k), list):
                obj = obj[k]
                break
        else:
            return None, "dict_not_list"
    if not isinstance(obj, list):
        return None, "not_a_list"
    return [r for r in obj if isinstance(r, dict)], None


def validate_record(rec):
    errs = []
    if REQUIRED - set(rec):
        errs.append("missing:" + str(sorted(REQUIRED - set(rec))))
    st = str(rec.get("status", "")).lower().strip()
    if st and st not in VALID_STATUS:
        errs.append("bad_status:" + st)
    if not str(rec.get("drug", "")).strip():
        errs.append("empty_drug")
    return errs


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def is_faithful(drug, note):
    if not drug:
        return False
    d, n = _norm(drug), _norm(note)
    if d and d in n:
        return True
    return len(d) >= 6 and d[:6] in n


def faithfulness_report(records, note):
    flags = [(r.get("drug"), is_faithful(r.get("drug"), note)) for r in records]
    bad = [d for d, ok in flags if not ok]
    return {"n": len(flags), "hallucinated": len(bad),
            "rate": round(len(bad) / len(flags), 3) if flags else 0.0,
            "examples": bad[:5]}
