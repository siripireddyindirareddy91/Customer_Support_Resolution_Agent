"""Local-only fixture data. Replace with tenant-scoped repository adapters in deployment."""

ORDERS = {
    "ORD-1001": {
        "id": "ORD-1001",
        "customer_id": "CUS-1001",
        "status": "shipped",
        "placed_at": "2026-10-02T10:15:00Z",
        "items": [{"name": "Everyday Backpack", "quantity": 1, "price": 64.0}],
        "total": 64.0,
    },
    "ORD-1002": {
        "id": "ORD-1002",
        "customer_id": "CUS-1001",
        "status": "delivered",
        "placed_at": "2026-09-27T12:00:00Z",
        "items": [{"name": "Ceramic Travel Mug", "quantity": 2, "price": 22.5}],
        "total": 45.0,
    },
    "ORD-2001": {
        "id": "ORD-2001",
        "customer_id": "CUS-1002",
        "status": "delivered",
        "placed_at": "2026-10-01T09:30:00Z",
        "items": [{"name": "Desk Lamp", "quantity": 1, "price": 38.0}],
        "total": 38.0,
    },
}

DELIVERIES = {
    "ORD-1001": {
        "status": "in_transit",
        "carrier": "Parcel Post",
        "tracking_number": "PP-884120",
        "estimated_delivery": "2026-10-08",
        "events": ["Oct 05: Shipment accepted", "Oct 06: Arrived at regional hub"],
    },
    "ORD-1002": {
        "status": "delivered",
        "carrier": "Parcel Post",
        "tracking_number": "PP-882014",
        "delivered_at": "2026-09-29T16:42:00Z",
        "events": ["Sep 29: Delivered"],
    },
    "ORD-2001": {
        "status": "delivered",
        "carrier": "CityShip",
        "tracking_number": "CS-220901",
        "delivered_at": "2026-10-04T14:10:00Z",
        "events": ["Oct 04: Delivered"],
    },
}