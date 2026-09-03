"""Evaluation harness for medication extraction."""
import pandas as pd
from collections import Counter


def _key(r, level):
    base = (r["note_id"], str(r["normalized"]).lower().strip())
    return base if level == "drug" else base + (str(r["status"]).lower().strip(),)


def match(pred_df, gold_df, level="drug"):
    pool = {}
    for i, r in gold_df.iterrows():
        pool.setdefault(_key(r, level), []).append(i)
    tp, fp, used = [], [], set()
    for j, r in pred_df.iterrows():
        candidates = pool.get(_key(r, level), [])
        hit = next((g for g in candidates if g not in used), None)
        if hit is None:
            fp.append(j)
        else:
            used.add(hit)
            tp.append((j, hit))
    fn = [i for i in gold_df.index if i not in used]
    return tp, fp, fn


def prf(tp, fp, fn):
    p = len(tp) / (len(tp) + len(fp)) if (len(tp) + len(fp)) else 0.0
    r = len(tp) / (len(tp) + len(fn)) if (len(tp) + len(fn)) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3),
            "tp": len(tp), "fp": len(fp), "fn": len(fn)}


def evaluate(pred_df, gold_df):
    levels = {lv: prf(*match(pred_df, gold_df, lv)) for lv in ["drug", "drug+status"]}
    tp, fp, fn = match(pred_df, gold_df, "drug")
    attrs = {}
    for a in ["dose", "frequency", "status"]:
        num = den = 0
        for j, i in tp:
            g, p = gold_df.loc[i, a], pred_df.loc[j, a]
            gv = None if pd.isna(g) or str(g).strip() == "" else str(g).lower().strip()
            pv = None if pd.isna(p) or str(p).strip() == "" else str(p).lower().strip()
            if gv is None and pv is None:
                continue
            den += 1
            num += int(gv == pv)
        attrs[a] = {"accuracy": round(num / den, 3) if den else None, "n": den}
    return {"levels": levels, "attributes": attrs, "matches": (tp, fp, fn)}
