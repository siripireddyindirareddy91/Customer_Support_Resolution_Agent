"""Queryable domain records synchronized with the original API snapshots."""
from sqlalchemy import JSON, Column, Float, ForeignKey, Integer, String, Table, Text, delete, select

from .sources import lookup_carrier_status, lookup_customer_history

ROLES = ("ADMIN", "SUPPORT_MANAGER", "SUPPORT_AGENT", "AUDITOR")


class DomainStore:
    def __init__(self, metadata):
        self.tables = {}

        def table(name, *columns):
            result = Table(name, metadata, Column("id", String(128), primary_key=True), *columns)
            self.tables[name] = result
            return result

        def fk(name, target, nullable=False):
            return Column(name, String(128), ForeignKey(target + ".id"), index=True, nullable=nullable)

        def label(name):
            return Column(name, String(128), nullable=False)

        table("roles", label("name"))
        table("user_roles", fk("user_id", "users", False), fk("role_id", "roles"))
        table("customers", label("reference"), Column("simulated", Integer, nullable=False))
        table("order_items", fk("order_id", "orders"), fk("customer_id", "customers"),
              label("product"), Column("quantity", Integer, nullable=False))
        table("shipments", fk("order_id", "orders"), fk("customer_id", "customers"),
              label("carrier"), label("expected_date"), label("status"))
        table("shipment_tracking_links", fk("shipment_id", "shipments"), fk("event_id", "tracking_events"))
        table("carrier_updates", fk("shipment_id", "shipments"), label("status"), Column("exception", Text),
              Column("evidence", JSON, nullable=False))
        table("support_tickets", fk("customer_id", "customers"), fk("order_id", "orders"),
              label("status"), Column("evidence", JSON, nullable=False))
        table("investigation_links", fk("investigation_id", "investigations"), fk("owner_id", "users"),
              fk("order_id", "orders", True), label("status"), label("created_at"))
        table("investigation_agent_runs", fk("investigation_id", "investigations"), label("agent"),
              label("status"), label("executed_at"), Column("duration_ms", Float, nullable=False),
              Column("trace", JSON, nullable=False))
        table("classifications", fk("investigation_id", "investigations"), label("issue_type"), label("severity"),
              Column("confidence", Float, nullable=False), Column("reason", Text, nullable=False))
        table("resolutions", fk("investigation_id", "investigations"), label("action"),
              Column("draft", Text, nullable=False), label("draft_source"), Column("citations", JSON, nullable=False))
        table("human_approvals", fk("investigation_id", "investigations"), fk("reviewer_id", "users", True),
              label("action"), label("decided_at"), Column("notes", Text, nullable=False))
        table("policy_chunks", fk("document_id", "policy_documents"), label("section"), label("version"),
              label("effective_date"), Column("passage", Text, nullable=False), Column("evidence", JSON, nullable=False))
        table("evaluation_cases", label("order_reference"), label("category"), label("expected_issue"),
              Column("expected_review", Integer, nullable=False), Column("complaint", Text, nullable=False))
        table("evaluation_results", fk("run_id", "evaluation_runs"), fk("case_id", "evaluation_cases"),
              label("actual_issue"), Column("actual_review", Integer, nullable=False),
              Column("passed", Integer, nullable=False))
        table("audit_investigation_links", fk("investigation_id", "investigations"), fk("event_id", "audit_events"))

    def write(self, connection, table_name, identifier, **values):
        table = self.tables[table_name]
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        upsert = pg_insert if connection.dialect.name == "postgresql" else sqlite_insert
        statement = upsert(table).values(id=identifier, **values)
        connection.execute(statement.on_conflict_do_update(index_elements=["id"], set_=values))

    def read(self, connection, name, **filters):
        table = self.tables[name]
        return connection.execute(select(table).filter_by(**filters)).mappings().all()

    def seed_roles(self, connection):
        for role in ROLES:
            self.write(connection, "roles", role, name=role)

    def order(self, connection, order, tracking):
        order_id, customer_id, shipment_id = (order[key] for key in ("order_id", "customer_id", "shipment_id"))
        self.write(connection, "customers", customer_id, reference=customer_id, simulated=1)
        self.write(connection, "order_items", order_id + "-1", order_id=order_id, customer_id=customer_id,
                   product=order["product"], quantity=1)
        self.write(connection, "shipments", shipment_id, order_id=order_id, customer_id=customer_id,
                   carrier=order["carrier"], expected_date=order["expected"], status=order["status"])
        for event in tracking:
            self.write(connection, "shipment_tracking_links", event["record_id"], shipment_id=shipment_id,
                       event_id=event["record_id"])
        carrier = lookup_carrier_status(order)
        self.write(connection, "carrier_updates", shipment_id, shipment_id=shipment_id, status=carrier["status"],
                   exception=carrier["exception"], evidence=carrier)
        for ticket in lookup_customer_history(order):
            self.write(connection, "support_tickets", ticket["record_id"], customer_id=customer_id,
                       order_id=order_id, status=ticket["status"], evidence=ticket)

    def case(self, connection, item):
        identifier = item["id"]
        order = item.get("order")
        self.write(connection, "investigation_links", identifier, investigation_id=identifier, owner_id=item["owner"],
                   order_id=order["order_id"] if order else None, status=item["status"], created_at=item["created_at"])
        if item.get("trace"):
            for index, stage in enumerate(item.get("trace", []), 1):
                run_id = item.get("run_thread") or item.get("thread") or identifier
                self.write(connection, "investigation_agent_runs", f"{run_id}-{index}", investigation_id=identifier,
                           agent=stage["agent"], status=stage["status"], executed_at=stage["at"],
                           duration_ms=stage["duration_ms"], trace=stage)
        if item.get("classification"):
            result = item["classification"]
            self.write(connection, "classifications", identifier, investigation_id=identifier,
                       issue_type=result["issue_type"], severity=result["severity"],
                       confidence=result["confidence"], reason=result["reasoning"])
        if item.get("resolution"):
            result = item["resolution"]
            self.write(connection, "resolutions", identifier, investigation_id=identifier, action=result["action"],
                       draft=result["draft"], draft_source=result.get("draft_source", "template"), citations=result["citations"])
        if item["status"] == "Queued":
            for name in ("classifications", "resolutions"):
                table = self.tables[name]
                connection.execute(delete(table).where(table.c.id == identifier))
        for decision in (item.get("decision"), item.get("escalation")):
            if decision:
                key = f"{identifier}:{decision['action']}:{decision['at']}"
                self.write(connection, "human_approvals", key, investigation_id=identifier, reviewer_id=decision["actor"],
                           action=decision["action"], decided_at=decision["at"], notes=decision["notes"])

    def save(self, connection, name, item):
        identifier = item["id"]
        if name == "users":
            self.write(connection, "user_roles", identifier, user_id=identifier, role_id=item["role"])
        elif name == "investigations":
            self.case(connection, item)
        elif name == "policy_documents":
            for chunk in item["chunks"]:
                self.write(connection, "policy_chunks", f"{identifier}:{chunk['section']}", document_id=identifier,
                           section=chunk["section"], version=chunk["version"], effective_date=chunk["effective_date"],
                           passage=chunk["passage"], evidence=chunk)
        elif name == "audit_events":
            self.write(connection, "audit_investigation_links", identifier, event_id=identifier,
                       investigation_id=item["investigation_id"])
        elif name == "evaluation_runs":
            for index, result in enumerate(item["cases"], 1):
                case_id = self.evaluation_case(connection, index, result)
                self.write(connection, "evaluation_results", f"{identifier}-{index}", run_id=identifier, case_id=case_id,
                           actual_issue=result["actual_issue"], actual_review=int(result["actual_review"]),
                           passed=int(result["passed"]))

    def evaluation_case(self, connection, index, item):
        identifier = f"EVAL-{index:02d}"
        self.write(connection, "evaluation_cases", identifier, order_reference=item["order_id"], category=item["category"],
                   expected_issue=item["expected_issue"], expected_review=int(item["expected_review"]),
                   complaint=item["complaint"])
        return identifier
