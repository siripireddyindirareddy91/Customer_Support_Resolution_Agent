"""Optional API-backed models. The default deployment works without model credentials."""
import json
import os
from urllib.request import Request, urlopen

from langchain_core.embeddings import Embeddings


def model_request(path, body):
    base = os.environ["MODEL_API_BASE"].rstrip("/")
    request = Request(base + path, data=json.dumps(body).encode(), headers={
        "Authorization": "Bearer " + os.environ["MODEL_API_KEY"],
        "Content-Type": "application/json",
    })
    with urlopen(request, timeout=8) as response:
        return json.load(response)


class PolicyEmbeddings(Embeddings):
    def embed_documents(self, texts):
        result = model_request("/embeddings", {"model": os.environ["EMBEDDING_MODEL"], "input": texts})
        return [row["embedding"] for row in sorted(result["data"], key=lambda row: row["index"])]

    def embed_query(self, text):
        return self.embed_documents([text])[0]


def enabled(variable):
    return all(os.getenv(key) for key in ("MODEL_API_BASE", "MODEL_API_KEY", variable))
