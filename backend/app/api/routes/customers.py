from fastapi import APIRouter

from backend.app.services.demo_data import ORDERS

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("")
def list_customers() -> dict:
    customer_ids = sorted({str(order["customer_id"]) for order in ORDERS.values()})
    return {
        "items": [{"customer_id": customer_id, "orders": sum(order["customer_id"] == customer_id for order in ORDERS.values()), "source": "seed data"} for customer_id in customer_ids],
        "source": "seed data",
    }