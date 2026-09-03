"""Rule-based medication extractor."""
import re
from sectionizer import split_sections

BRAND2GENERIC = {'lasix': 'furosemide', 'synthroid': 'levothyroxine', 'vicodin': 'hydrocodone-acetaminophen', 'coumadin': 'warfarin', 'lipitor': 'atorvastatin', 'colace': 'docusate', 'advair': 'fluticasone-salmeterol', 'claritin': 'loratadine', 'toprol': 'metoprolol', 'lopressor': 'metoprolol', 'flomax': 'tamsulosin', 'paxil': 'paroxetine', 'lantus': 'insulin glargine', 'prevacid': 'lansoprazole', 'proventil': 'albuterol', 'humulin': 'insulin', 'zestril': 'lisinopril', 'tylenol': 'acetaminophen', 'motrin': 'ibuprofen', 'glucophage': 'metformin', 'prilosec': 'omeprazole', 'norvasc': 'amlodipine', 'zocor': 'simvastatin', 'plavix': 'clopidogrel', 'bactrim': 'sulfamethoxazole-trimethoprim', 'zyrtec': 'cetirizine', 'allegra': 'fexofenadine', 'protonix': 'pantoprazole', 'ambien': 'zolpidem', 'neurontin': 'gabapentin', 'percocet': 'oxycodone-acetaminophen', 'lortab': 'hydrocodone-acetaminophen', 'nexium': 'esomeprazole', 'ativan': 'lorazepam', 'xanax': 'alprazolam', 'prozac': 'fluoxetine', 'zoloft': 'sertraline', 'aricept': 'donepezil', 'atrovent': 'ipratropium', 'macrodantin': 'nitrofurantoin', 'pravachol': 'pravastatin', 'glucotrol': 'glipizide', 'detrol': 'tolterodine', 'monopril': 'fosinopril', 'tapazole': 'methimazole', 'demerol': 'meperidine', 'toradol': 'ketorolac', 'feosol': 'ferrous sulfate', 'celebrex': 'celecoxib', 'lovenox': 'enoxaparin', 'singulair': 'montelukast', 'fosamax': 'alendronate', 'actos': 'pioglitazone', 'diovan': 'valsartan', 'cozaar': 'losartan', 'altace': 'ramipril', 'imdur': 'isosorbide', 'nitrostat': 'nitroglycerin', 'dilantin': 'phenytoin', 'depakote': 'valproate', 'risperdal': 'risperidone', 'seroquel': 'quetiapine', 'zyprexa': 'olanzapine', 'wellbutrin': 'bupropion', 'effexor': 'venlafaxine', 'celexa': 'citalopram', 'lexapro': 'escitalopram', 'restoril': 'temazepam', 'flonase': 'fluticasone', 'serevent': 'salmeterol', 'pepcid': 'famotidine', 'zantac': 'ranitidine', 'reglan': 'metoclopramide', 'phenergan': 'promethazine', 'zofran': 'ondansetron', 'cipro': 'ciprofloxacin', 'levaquin': 'levofloxacin', 'augmentin': 'amoxicillin-clavulanate', 'keflex': 'cephalexin', 'zithromax': 'azithromycin', 'diflucan': 'fluconazole', 'valtrex': 'valacyclovir'}
GENERICS = {'montelukast', 'thiamine', 'venlafaxine', 'dexamethasone', 'levetiracetam', 'methimazole', 'allopurinol', 'atorvastatin', 'metoclopramide', 'carvedilol', 'felodipine', 'clindamycin', 'docusate', 'lorazepam', 'trazodone', 'labetalol', 'spironolactone', 'penicillin', 'valsartan', 'enoxaparin', 'memantine', 'ketorolac', 'levothyroxine', 'amlodipine', 'digoxin', 'pravastatin', 'warfarin', 'hydroxyzine', 'loratadine', 'quetiapine', 'gabapentin', 'glyburide', 'ferrous sulfate', 'phenytoin', 'propranolol', 'ciprofloxacin', 'lisinopril', 'potassium', 'levofloxacin', 'methylprednisolone', 'lovastatin', 'nystatin', 'methotrexate', 'estradiol', 'clonidine', 'acetaminophen', 'sertraline', 'hydralazine', 'paroxetine', 'ibuprofen', 'meloxicam', 'isosorbide', 'fexofenadine', 'bupropion', 'tizanidine', 'losartan', 'diazepam', 'nitrofurantoin', 'pantoprazole', 'metoprolol', 'ranitidine', 'hydrochlorothiazide', 'nitroglycerin', 'escitalopram', 'amiodarone', 'famotidine', 'albuterol', 'iron', 'multivitamin', 'sildenafil', 'donepezil', 'doxycycline', 'magnesium', 'clopidogrel', 'baclofen', 'zolpidem', 'azithromycin', 'niacin', 'ramipril', 'oxycodone', 'prednisone', 'heparin', 'metformin', 'fluticasone', 'sulfa', 'cephalexin', 'amoxicillin', 'glipizide', 'amitriptyline', 'finasteride', 'olanzapine', 'furosemide', 'atenolol', 'cyclobenzaprine', 'aspirin', 'meclizine', 'promethazine', 'celecoxib', 'cetirizine', 'codeine', 'oxybutynin', 'salmeterol', 'tramadol', 'fluoxetine', 'methadone', 'fluconazole', 'insulin', 'citalopram', 'colchicine', 'alprazolam', 'tamsulosin', 'fentanyl', 'lansoprazole', 'calcium', 'simvastatin', 'morphine', 'ipratropium', 'hydrocodone', 'naproxen', 'omeprazole', 'ondansetron', 'enalapril', 'theophylline', 'risperidone', 'folic acid', 'budesonide'}
FREQ_CANON = {'bid': 'twice daily', 'b.i.d.': 'twice daily', 'twice a day': 'twice daily', 'tid': 'three times daily', 't.i.d.': 'three times daily', 'three times a day': 'three times daily', 'qid': 'four times daily', 'q.i.d.': 'four times daily', 'four times a day': 'four times daily', 'qd': 'daily', 'q.d.': 'daily', 'daily': 'daily', 'once a day': 'daily', 'once daily': 'daily', 'qhs': 'at bedtime', 'q.h.s.': 'at bedtime', 'at bedtime': 'at bedtime', 'nightly': 'at bedtime', 'prn': 'as needed', 'p.r.n.': 'as needed', 'as needed': 'as needed', 'qod': 'every other day', 'every other day': 'every other day', 'weekly': 'weekly', 'in the morning': 'in the morning'}
ROUTE_CANON = {'po': 'oral', 'p.o.': 'oral', 'by mouth': 'oral', 'orally': 'oral', 'iv': 'intravenous', 'intravenous': 'intravenous', 'intravenously': 'intravenous', 'im': 'intramuscular', 'intramuscular': 'intramuscular', 'subq': 'subcutaneous', 'sub-q': 'subcutaneous', 'subcutaneous': 'subcutaneous', 'subcutaneously': 'subcutaneous', 'topical': 'topical', 'topically': 'topical', 'inhale': 'inhaled', 'inhaled': 'inhaled', 'puff': 'inhaled', 'patch': 'transdermal', 'transdermal': 'transdermal', 'sublingual': 'sublingual', 'pr': 'rectal', 'per rectum': 'rectal', 'p.r.': 'rectal'}
SECTION_STATUS = {'medications': 'active', 'discharge_medications': 'discharge', 'allergies': 'allergy', 'family_history': 'family', 'social_history': 'context', 'hpi': 'mentioned', 'hospital_course': 'inpatient', 'plan': 'planned', 'assessment_plan': 'planned', 'assessment': 'mentioned', 'pmh': 'historical', 'discharge_instructions': 'discharge'}
SKIP_SECTIONS = {'ros', 'vitals', '_preamble', 'labs', 'physical_exam'}
SPLIT_RE = re.compile(',(?![^()]*\\))|;|\\.\\s+(?=[A-Z0-9])|\\band\\b(?=\\s+[A-Z])')
DOSE_RE = re.compile('\\b(\\d+(?:\\.\\d+)?|one-half|one|two|three)\\s*(mg|mcg|g|gm|units?|mL|ml|mEq|%)\\b', re.I)
ROUTE_RE = re.compile('\\b(p\\.?o\\.?|by mouth|orally|IV|intravenous(?:ly)?|IM|intramuscular|sub\\s?-?q|subcutaneous(?:ly)?|topical(?:ly)?|inhaled?|per rectum|p\\.?r\\.?|sublingual|transdermal|patch|puff)\\b', re.I)
FREQ_RE = re.compile('\\b(b\\.?i\\.?d\\.?|t\\.?i\\.?d\\.?|q\\.?i\\.?d\\.?|q\\.?d\\.?|q\\.?h\\.?s\\.?|q\\.?o\\.?d\\.?|p\\.?r\\.?n\\.?|daily|twice a day|three times a day|four times a day|once a day|once daily|every\\s+\\w+\\s+hours?|at bedtime|nightly|in the morning|as needed|every other day|weekly)\\b', re.I)
NEG_CUES = re.compile("\\b(no|not|denies|denied|without|never|allergic to|allergy to|intoleran\\w+|reaction to|discontinued?|stopped|held?|d/c\\'?d?)\\b", re.I)
PAST_CUES = re.compile('\\b(previously|formerly|in the past|used to|had been|was on|prior to admission|history of)\\b', re.I)


LEXICON = {b: {"generic": g, "is_brand": True} for b, g in BRAND2GENERIC.items()}
LEXICON.update({g: {"generic": g, "is_brand": False} for g in GENERICS})


def segment_medication_list(text):
    parts, pos = [], 0
    for m in SPLIT_RE.finditer(text):
        seg = text[pos:m.start()]
        if seg.strip():
            parts.append((pos, seg))
        pos = m.end()
    if text[pos:].strip():
        parts.append((pos, text[pos:]))
    return parts


def find_drugs(segment):
    low = segment.lower()
    hits = [(m.start(), m.end(), term, info)
            for term, info in LEXICON.items()
            for m in re.finditer(r"\b" + re.escape(term) + r"\b", low)]
    hits.sort()
    kept = []
    for h in hits:
        if kept and h[0] < kept[-1][1]:
            if (h[1] - h[0]) > (kept[-1][1] - kept[-1][0]):
                kept[-1] = h
            continue
        kept.append(h)
    return kept


def _canon(match, table):
    if not match:
        return None
    key = match.group(1).lower().strip()
    return table.get(key, table.get(key.replace(".", ""), key))


def extract_medications(note):
    results = []
    for section, body in split_sections(note).items():
        if section in SKIP_SECTIONS or section.startswith("exam:"):
            continue
        base_status = SECTION_STATUS.get(section, "mentioned")
        for _, segment in segment_medication_list(body):
            drugs = find_drugs(segment)
            if not drugs:
                continue
            multi = len(drugs) > 1
            dose = DOSE_RE.search(segment)
            route = ROUTE_RE.search(segment)
            freq = FREQ_RE.search(segment)
            negated = bool(NEG_CUES.search(segment))
            past = bool(PAST_CUES.search(segment))
            for s, e, term, info in drugs:
                status = base_status
                if section == "allergies":
                    status = "allergy"
                elif negated:
                    status = "negated"
                elif past:
                    status = "historical"
                results.append({
                    "drug_text": segment[s:e],
                    "normalized": info["generic"],
                    "is_brand": info["is_brand"],
                    "dose": dose.group(0).strip() if (dose and not multi) else None,
                    "route": _canon(route, ROUTE_CANON) if not multi else None,
                    "frequency": _canon(freq, FREQ_CANON) if not multi else None,
                    "section": section,
                    "status": status,
                    "attrs_ambiguous": multi,
                    "snippet": " ".join(segment.split())[:120],
                })
    seen, dedup = set(), []
    for r in results:
        k = (r["normalized"], r["section"], r["status"], r["dose"])
        if k not in seen:
            seen.add(k)
            dedup.append(r)
    return dedup
