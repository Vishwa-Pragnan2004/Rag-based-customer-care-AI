from .database import book_appointment, get_ticket_status, lookup_customer, escalate_to_human
def get_service_info(service_type: str) -> dict:
    pricing = {"installation": "?1500", "repair": "?500 visit + parts", "amc": "?2500/yr", "gas_refill": "?2000"}
    return {"service": service_type, "price": pricing.get(service_type, "Unknown")}
def get_warranty_info() -> dict:
    return {"installation": "30 days", "repair": "90 days parts & labor"}

_TOOLS = {
    "book_appointment": book_appointment,
    "get_ticket_status": get_ticket_status,
    "lookup_customer": lookup_customer,
    "get_service_info": get_service_info,
    "escalate_to_human": escalate_to_human,
    "get_warranty_info": get_warranty_info
}
def call_tool(name: str, args: dict): return _TOOLS[name](**args) if name in _TOOLS else {"error": "Tool not found"}
