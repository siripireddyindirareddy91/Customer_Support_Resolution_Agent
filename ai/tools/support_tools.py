from langchain_core.tools import tool

from backend.app.services.demo_data import DELIVERIES, ORDERS


@tool
def get_order(order_id: str, customer_id: str) -> dict | None:
    """Return an order only when it belongs to the authenticated customer."""
    order = ORDERS.get(order_id)
    if order is None or order["customer_id"] != customer_id:
        return None
    return {key: value for key, value in order.items() if key != "customer_id"}


@tool
def get_delivery_status(order_id: str, customer_id: str) -> dict | None:
    """Return delivery tracking only after verifying customer ownership."""
    order = ORDERS.get(order_id)
    if order is None or order["customer_id"] != customer_id:
        return None
    return DELIVERIES.get(order_id)


ORDER_TOOLS = {"get_order": get_order, "get_delivery_status": get_delivery_status}