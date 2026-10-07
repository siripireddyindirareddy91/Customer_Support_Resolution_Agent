# LangGraph architecture

`ai/langgraph/workflow.py` compiles a typed state graph. The normal path is input guardrail -> intent -> supervisor -> planner -> router -> tools -> policy -> resolution -> critic -> validator -> response. Human escalation skips external lookups and goes directly to a structured escalated response. Failed validation follows one bounded replan step and then asks for human review.

The graph stores structured operational fields only; it does not persist chain-of-thought. It currently compiles without a checkpoint saver, so restart recovery is not enabled. Add a PostgreSQL checkpointer and a retention policy before production use.