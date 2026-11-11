from datetime import UTC, datetime, timedelta

SCENARIOS = ("delayed", "failed", "conflict", "lost", "transit", "delivered", "transit", "damaged")
AGENTS = ("Order Lookup", "Delivery Classification", "Policy Retrieval", "Resolution & Handoff")
POLICIES = [
    ("P-01", "Delivery delays", "MINOR_DELAY MAJOR_DELAY ON_TIME", "Share the verified delivery estimate. Open a carrier investigation when delivery is more than two days overdue."),
    ("P-02", "Lost shipments", "LOST_SUSPECTED", "Open a carrier trace for a missing shipment. Refer confirmed loss to an authorized reviewer."),
    ("P-03", "Damaged packages", "DAMAGED", "Request photos of the packaging and goods. Refer replacement eligibility to a reviewer."),
    ("P-04", "Refund eligibility", "REFUND", "A reviewer must verify eligibility and evidence before recommending a refund."),
    ("P-05", "Replacement eligibility", "REPLACEMENT DAMAGED", "A reviewer must verify the order and document the damage or loss before approving a replacement."),
    ("P-06", "Delivery attempts", "DELIVERY_FAILED", "Verify the delivery instructions and ask the carrier to confirm its next attempt."),
    ("P-07", "Escalation", "STATUS_CONFLICT UNKNOWN", "Route contradictory or incomplete evidence to a support reviewer for verification."),
    ("P-08", "Suspicious claims", "FRAUD", "Refer suspicious claims to a reviewer. Verify identity and evidence before changing any account or order."),
]


def record(source, identifier, **data):
    return dict(source=source, record_id=identifier, retrieved_at=datetime.now(UTC).isoformat(),
                access="support", freshness="synthetic snapshot", simulated=True, **data)


def lookup_order(order_id):
    if order_id not in order_ids():
        return None
    index = int(order_id[-5:]) - 10452
    today = datetime.now(UTC).date()
    scenario = SCENARIOS[index % len(SCENARIOS)]
    return record("Order Management", order_id, order_id=order_id, customer_id=f"C-{1000 + index}",
                  shipment_id=f"SHP-{83400 + index}", carrier=("Northline", "ParcelBridge")[index % 2],
                  product=("Studio headphones", "Travel backpack", "Desk lamp")[index % 3],
                  order_date=str(today - timedelta(days=9)), payment="Paid",
                  expected=str(today + timedelta(days=-4 if scenario in {"delayed", "lost"} else 1)),
                  status=scenario)


def order_ids():
    return [f"ORD-{i}" for i in range(10452, 10482)]


def lookup_tracking(order):
    shipment = order["shipment_id"]
    status = order["status"]
    now = datetime.now(UTC)
    last = now - timedelta(days=6 if status == "lost" else 0)
    events = [("Manifest received", now - timedelta(days=8)), ("In transit", now - timedelta(days=7)),
              ({"failed": "Delivery attempted", "conflict": "Delivered", "delivered": "Delivered",
                "damaged": "Damage reported", "delayed": "Operational hold"}.get(status, "In transit"), last)]
    return [record("Shipment Tracking", f"{shipment}-{i}", status=label, timestamp=at.isoformat())
            for i, (label, at) in enumerate(events, 1)]


def lookup_carrier_status(order):
    return record("Carrier Status", order["shipment_id"], status=order["status"],
                  exception={"conflict": "Return to sender", "lost": "No recent scan"}.get(order["status"]))


def lookup_customer_history(order):
    index = int(order["order_id"][-5:]) - 10452
    return [record("Customer Support", f"TKT-{7000 + index}", category="Delivery inquiry",
                   status="Closed")] if index < 15 else []
