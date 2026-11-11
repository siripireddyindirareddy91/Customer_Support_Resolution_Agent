import logging
import re
from functools import lru_cache

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore

from .providers import PolicyEmbeddings, enabled
from .sources import POLICIES

logger = logging.getLogger(__name__)


def words(text):
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def demo_policies():
    return [dict(id=key, name=name, version="1.0", effective_date="2025-01-01", section="1",
                 tags=tags, passage=passage, source="Synthetic Support Policy KB")
            for key, name, tags, passage in POLICIES]


@lru_cache(maxsize=1)
def semantic_store():
    store = InMemoryVectorStore(PolicyEmbeddings())
    store.add_documents([Document(page_content=policy["name"] + "\n" + policy["passage"], metadata=policy)
                         for policy in demo_policies()])
    return store


def retrieve(query, custom, issue_lookup=False):
    terms = words(query)
    if not terms:
        return []
    if enabled("EMBEDDING_MODEL") and not custom and not issue_lookup:
        try:
            found = semantic_store().similarity_search_with_score(query, k=5)
            return [{**document.metadata, "score": round(float(score), 3)}
                    for document, score in found if score >= .35]
        except (ImportError, OSError, KeyError, TypeError, ValueError):
            logger.warning("Semantic policy search unavailable. Using lexical retrieval.")

    matches = []
    for policy in demo_policies() + custom:
        tags = words(policy["tags"])
        indexed = tags if issue_lookup else tags | words(policy["name"] + " " + policy["passage"])
        overlap = terms & indexed
        if overlap:
            matches.append({**policy, "score": round(len(overlap) / len(terms), 3)})
    return sorted(matches, key=lambda item: item["score"], reverse=True)[:5]
