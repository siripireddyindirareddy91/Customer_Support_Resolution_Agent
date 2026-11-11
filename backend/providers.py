"""Optional API-backed models. The default deployment works without model credentials."""
import json
import logging
import os
import re
from urllib.request import Request, urlopen

from langchain_core.embeddings import Embeddings


def model_request(path, body, gateway_token=None):
    base = (os.getenv("MODEL_API_BASE") or "https://ai-gateway.vercel.sh/v1").rstrip("/")
    api_key = os.getenv("MODEL_API_KEY") or gateway_token
    request = Request(base + path, data=json.dumps(body).encode(), headers={
        "Authorization": "Bearer " + api_key,
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


def generate_draft(action, reason, fallback, gateway_token=None):
    if not enabled("DRAFT_MODEL") and not (gateway_token and os.getenv("DRAFT_MODEL")):
        return fallback, "template"
    try:
        result = model_request("/chat/completions", {
            "model": os.environ["DRAFT_MODEL"],
            "max_tokens": 700,
            "messages": [
                {"role": "system", "content": (
                    "Write a concise customer support reply. Use only the verified reason and next step. "
                    "Describe the action as a recommendation. Never claim an action has already occurred, "
                    "promise compensation, add tracking facts, ask for sensitive data, or include links. "
                    "Return only the customer-facing text."
                )},
                {"role": "user", "content": json.dumps({"verified_reason": reason, "next_step": action})},
            ],
        }, gateway_token)
        raw = result["choices"][0]["message"]["content"] or ""
        draft = re.sub(r"<think>.*?</think>", "", raw, flags=re.S).strip()
        if 20 <= len(draft) <= 1200 and not re.search(r"https?://|[<>]", draft, re.I):
            return draft, "llm"
    except (OSError, KeyError, IndexError, TypeError, ValueError, AttributeError) as error:
        logging.getLogger(__name__).warning("Draft provider returned %s. Using the evidence-based template.",
                                            getattr(error, "code", type(error).__name__))
    return fallback, "template"
