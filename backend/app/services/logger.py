import json
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

# Setup File Logging
logging.basicConfig(filename='../logs/security_audit.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# MongoDB Setup
client = AsyncIOMotorClient(settings.MONGODB_URI)
db = client["SSA_Security"]
audit_collection = db["logs"]

async def init_audit_log(request_id: str, user_context: dict, ip_address: str = None):
    """Initializes a single document for the entire request lifecycle."""
    try:
        log_data = {
            "request_id": request_id,
            "timestamp": datetime.utcnow(),
            "user_context": {
                "email": user_context.get("email"),
                "name": user_context.get("name"),
                "role": user_context.get("role"),
                "department": user_context.get("department")
            },
            "pipeline_events": [],
            "final_status": "PENDING",
            "latency_ms": 0
        }
        if ip_address is not None:
            log_data["ip_address"] = ip_address
            
        await audit_collection.insert_one(log_data)
        logging.info(f"AUDIT_START: {request_id} for {user_context.get('email')}")
    except Exception as e:
        logging.error(f"Failed to init audit log: {str(e)}")

async def log_pipeline_event(request_id: str, layer: str, status: str, details: dict = None):
    """Adds a specific event to the request's pipeline_events array."""
    event = {
        "layer": layer.upper(),
        "status": status.upper(),
        "timestamp": datetime.utcnow()
    }
    if details:
        event["details"] = details
        
    await audit_collection.update_one(
        {"request_id": request_id},
        {"$push": {"pipeline_events": event}}
    )
    logging.info(f"AUDIT_EVENT: {request_id} - {layer} - {status}")

async def finalize_audit_log(
    request_id: str, 
    final_status: str, 
    latency_ms: int,
    attack_type: str = None,
    entry_point: str = None,
    risk_level: str = None,
    root_cause: str = None,
    ip_address: str = None
):
    """Sets the final outcome and latency of the request."""
    try:
        set_fields = {
            "final_status": final_status.upper(),
            "latency_ms": latency_ms
        }
        
        if attack_type is not None: set_fields["attack_type"] = attack_type
        if entry_point is not None: set_fields["entry_point"] = entry_point
        if risk_level is not None: set_fields["risk_level"] = risk_level
        if root_cause is not None: set_fields["root_cause"] = root_cause
        if ip_address is not None: set_fields["ip_address"] = ip_address

        await audit_collection.update_one(
            {"request_id": request_id},
            {
                "$set": set_fields
            }
        )
        logging.info(f"AUDIT_FINALIZE: {request_id} - {final_status} ({latency_ms}ms)")
    except Exception as e:
        logging.error(f"Failed to finalize audit log: {str(e)}")

# Legacy support if needed for other modules
async def log_event(request_id: str, event_type: str, details: dict, user_email: str = "Anonymous", department: str = "Unknown"):
    """Legacy wrapper for backward compatibility during transition."""
    await log_pipeline_event(request_id, event_type, "INFO", details)