# RAG architecture

The local knowledge base contains Markdown policy examples. `ai/rag/pipeline.py` scores documents by lexical term matches and returns the source filename with a bounded excerpt. The response includes the source name when guidance is used; no citation is created when no source matches.

This is a development retriever, not the requested production RAG pipeline. PDF/DOCX ingestion, access metadata, embeddings, pgvector, hybrid search, reranking, and citation-span validation are not yet implemented. Treat policy files as trusted, reviewed application content; uploaded or web-retrieved content must not be used until ingestion isolation and prompt-injection controls exist.