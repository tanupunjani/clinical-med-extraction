"""RAG normalization over a drug vocabulary."""
import numpy as np


class DrugNormalizer:
    def __init__(self, concepts, embedder, threshold=0.62):
        self.concepts = concepts.reset_index(drop=True)
        self.embedder = embedder
        self.threshold = threshold
        self.emb = embedder.encode(self.concepts["name"].tolist(),
                                   batch_size=256, normalize_embeddings=True)
        self._cache = {}

    def retrieve(self, query, k=5):
        q = self.embedder.encode([query], normalize_embeddings=True)[0]
        sims = self.emb @ q
        idx = np.argpartition(-sims, min(k, len(sims) - 1))[:k]
        idx = idx[np.argsort(-sims[idx])]
        return [{"rxcui": self.concepts.iloc[i]["RXCUI"],
                 "name": self.concepts.iloc[i]["name"],
                 "score": float(sims[i])} for i in idx]

    def normalize(self, surface, threshold=None):
        if surface in self._cache:
            return self._cache[surface]
        thr = self.threshold if threshold is None else threshold
        hits = self.retrieve(surface, k=5)
        if not hits or hits[0]["score"] < thr:
            out = {"normalized": None, "rxcui": None,
                   "score": hits[0]["score"] if hits else 0.0,
                   "needs_review": True,
                   "candidates": [h["name"] for h in hits[:3]]}
        else:
            top = hits[0]
            out = {"normalized": top["name"].lower(), "rxcui": top["rxcui"],
                   "score": top["score"], "needs_review": False,
                   "candidates": [h["name"] for h in hits[:3]]}
        self._cache[surface] = out
        return out


def recall_at_k(retrieved, truth, ks=(1, 3, 5)):
    return {f"recall@{k}": round(sum(1 for c, t in zip(retrieved, truth) if t in c[:k]) / len(truth), 3)
            for k in ks} if truth else {}


def mrr(retrieved, truth):
    if not truth:
        return None
    total = sum(1.0 / (c.index(t) + 1) for c, t in zip(retrieved, truth) if t in c)
    return round(total / len(truth), 3)
