# Data flow

1. The browser obtains a short-lived development token and sends a support message over HTTPS in a deployment.
2. FastAPI validates the token, validates the Pydantic request, and takes `customer_id` only from the signed subject.
3. LangGraph classifies and routes the request. The customer-scoped tools return only matching order records.
4. The local policy retriever returns snippets with their source filenames. Tool data and policy evidence are passed into a structured resolution and validation step.
5. The response is returned with safe workflow activity, evidence citations, and order context. No conversation is currently saved.