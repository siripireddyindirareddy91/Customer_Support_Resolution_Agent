from pathlib import Path

from fastapi import APIRouter

from ai.rag.pipeline import KNOWLEDGE_ROOT

router = APIRouter(prefix="/api/knowledge-base", tags=["knowledge base"])


@router.get("")
def list_knowledge_documents() -> dict:
    documents = []
    for path in sorted(KNOWLEDGE_ROOT.rglob("*.md")):
        documents.append({
            "document_id": path.relative_to(KNOWLEDGE_ROOT).as_posix(),
            "file_name": path.name,
            "category": path.parent.name.replace("_", " "),
            "bytes": path.stat().st_size,
            "source": "local markdown",
        })
    return {"items": documents, "source": "knowledge_base"}