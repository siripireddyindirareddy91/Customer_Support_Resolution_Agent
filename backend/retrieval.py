import logging
import re
from functools import lru_cache
from hashlib import blake2b

import faiss
import numpy as np

from .providers import PolicyEmbeddings, enabled
from .sources import POLICIES

logger = logging.getLogger(__name__)


def words(text):
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def demo_policies():
    return [dict(id=key, name=name, version="1.0", effective_date="2025-01-01", section="1",
                 tags=tags, passage=passage, source="Synthetic Support Policy KB")
            for key, name, tags, passage in POLICIES]


def local_vectors(texts):
    vectors = np.zeros((len(texts), 2048), dtype=np.float32)
    for index, text in enumerate(texts):
        for word in words(text):
            bucket = int.from_bytes(blake2b(word.encode(), digest_size=4).digest(), "little") % 2048
            vectors[index, bucket] += 1
    return vectors


@lru_cache(maxsize=32)
def semantic_store(texts, remote=False):
    vectors = np.asarray(PolicyEmbeddings().embed_documents(list(texts)) if remote else local_vectors(texts),
                         dtype=np.float32)
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    return index


def ranked(query, candidates, issue_lookup, remote=False):
    texts = tuple(item["tags"] if issue_lookup else " ".join((item["tags"], item["name"], item["passage"]))
                  for item in candidates)
    index = semantic_store(texts, remote) if not any(not item["id"].startswith("P-") for item in candidates) else None
    if index is None:
        vectors = local_vectors(texts)
        faiss.normalize_L2(vectors)
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
    query_vector = np.asarray([PolicyEmbeddings().embed_query(query)] if remote else local_vectors([query]),
                              dtype=np.float32)
    faiss.normalize_L2(query_vector)
    scores, positions = index.search(query_vector, min(5, len(candidates)))
    return [{**candidates[int(position)], "score": round(float(score), 3), "retriever": "faiss"}
            for score, position in zip(scores[0], positions[0]) if position >= 0 and score > (.35 if remote else 0)]


def retrieve(query, custom, issue_lookup=False):
    terms = words(query)
    if not terms:
        return []
    candidates = demo_policies() + custom
    if enabled("EMBEDDING_MODEL") and not custom and not issue_lookup:
        try:
            return ranked(query, candidates, False, remote=True)
        except (OSError, KeyError, RuntimeError, TypeError, ValueError):
            logger.warning("Embedding provider unavailable. Using local FAISS vectors.")
    candidates = [item for item in candidates if terms & (
        words(item["tags"]) if issue_lookup else words(" ".join((item["tags"], item["name"], item["passage"])))
    )]
    return ranked(query, candidates, issue_lookup) if candidates else []
