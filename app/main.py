import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="instructor.providers.gemini")

from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import uuid
from pydantic import BaseModel
from datetime import datetime

from app.config import settings
from app.layers.input_guard import check_input
from app.layers.policy_engine import check_policy
from app.layers.toxicity_guard import check_toxicity
from app.layers.pii_guard import scrub_pii
from app.layers.normalizer import normalize_text
from app.services.llm_service import generate_response
from app.services.logger import init_audit_log, log_pipeline_event, finalize_audit_log, client
from app.services.user_service import register_user_db, authenticate_user_db, get_current_user, require_super_admin, require_any_admin
from app.layers.semantic_guard import check_semantic_intent

# --- NEW: GUARDRAILS & LOGGING ---
import json
import os

def simple_langsmith_logger(user_input, risk_score, decision, final_response):
    """Basic local logging system (LangSmith-style)"""
    try:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_input": user_input,
            "risk_score": risk_score,
            "decision": decision,
            "final_response": final_response
        }
        with open("simple_audit.log", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Logging error: {e}")

async def apply_guardrails(response_text: str) -> str:
    """Apply Guardrails after LLM response. Fail-safe."""
    try:
        # Placeholder for actual guardrails logic
        # e.g., guard = Guard.from_string(...)
        # return guard.parse(response_text)
        return response_text
    except Exception as e:
        print(f"Guardrails error: {e}")
        return response_text # Fail-safe
# ---------------------------------

# 1. Initialize App
app = FastAPI(title=settings.app_name)

chat_db = client["SSA_Security"]["chats"]

# 2. Add CORS Middleware (Crucial for Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # local frontend
        "https://your-app.vercel.app"  # deployed frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def setup_data_retention():
    """Sets up MongoDB TTL indexes for automatic data cleanup."""
    retention_seconds = settings.RETENTION_DAYS * 24 * 60 * 60
    
    # # TTL Index for Audit Logs
    # await client["SSA_Security"]["logs"].create_index(
    #     "timestamp", 
    #     expireAfterSeconds=retention_seconds
    # )
    
    # # TTL Index for Chat History
    # await client["SSA_Security"]["chats"].create_index(
    #     "timestamp", 
    #     expireAfterSeconds=retention_seconds
    # )
    
    print(f"Data retention policy active: {settings.RETENTION_DAYS} days")

# Auth Models
class RegisterModel(BaseModel):
    email: str
    password: str
    name: str
    role: str
    department: str

class LoginModel(BaseModel):
    email: str
    password: str

class ChatMessageModel(BaseModel):
    message: str

class RefreshModel(BaseModel):
    refresh_token: str

# 3. Root Endpoint
@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.app_name} in {settings.ENVIRONMENT} mode"}

@app.post("/auth/register")
async def register(data: RegisterModel):
    result = await register_user_db(data.email, data.password, data.name, data.role, data.department)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.post("/auth/login")
async def login(data: LoginModel):
    result = await authenticate_user_db(data.email, data.password)
    if result["status"] == "error":
         raise HTTPException(status_code=401, detail=result["message"])
    return result

from app.services.user_service import refresh_token_db

@app.post("/auth/refresh")
async def refresh_session(data: RefreshModel):
    result = await refresh_token_db(data.refresh_token)
    if result["status"] == "error":
        raise HTTPException(status_code=401, detail=result["message"])
    return result

# 4. Chat Endpoints
@app.get("/chat/history")
async def get_chat_history(current_user: dict = Depends(get_current_user)):
    cursor = chat_db.find({"user_email": current_user["email"]}).sort("timestamp", 1)
    history = await cursor.to_list(length=100)
    for msg in history:
        msg["id"] = str(msg.pop("_id"))
    return history

@app.delete("/chat/history")
async def clear_chat_history(current_user: dict = Depends(get_current_user)):
    await chat_db.delete_many({"user_email": current_user["email"]})
    return {"status": "success", "message": "History cleared"}

@app.post("/chat")
async def chat_endpoint(data: ChatMessageModel, current_user: dict = Depends(get_current_user)):
    start_time = datetime.utcnow()
    request_id = str(uuid.uuid4())
    message = data.message
    role = current_user["role"]
    
    # 1. Initialize the audit trail for this request
    await init_audit_log(request_id, current_user)

    # Save User Context in chat history
    await chat_db.insert_one({"user_email": current_user["email"], "role": "user", "content": message, "timestamp": datetime.utcnow()})
    
    normalized_message = normalize_text(message)
    
    async def block_and_return(reason, layer):
        # Log the block in the pipeline
        await log_pipeline_event(request_id, layer, "BLOCKED", {"reason": reason, "message": normalized_message})
        
        # Finalize the log
        latency = (datetime.utcnow() - start_time).total_seconds() * 1000
        await finalize_audit_log(request_id, "BLOCKED", int(latency))
        
        system_msg = {"user_email": current_user["email"], "role": "system", "content": "Payload intercepted and destroyed.", "status": "BLOCKED", "reason": reason, "timestamp": datetime.utcnow()}
        await chat_db.insert_one(system_msg.copy())
        
        # --- NEW: SIMPLE LOGGING ---
        simple_langsmith_logger(message, 1.0, "BLOCK", f"Blocked by {layer}: {reason}")
        # ---------------------------
        
        return {"status": "BLOCKED", "reason": reason}

    # Pipeline Checks
    import asyncio
    
    if not await check_input(normalized_message): 
        return await block_and_return("Forbidden pattern detected (Static Input Guard)", "INPUT_GUARD")
    await log_pipeline_event(request_id, "INPUT_GUARD", "PASSED")
    
    if not await check_policy(normalized_message, role): 
        return await block_and_return("Role-based policy violation (Policy Engine)", "POLICY_ENGINE")
    await log_pipeline_event(request_id, "POLICY_ENGINE", "PASSED")
    
    # Run heavy LLM-based guards in PARALLEL to reduce latency
    try:
        toxicity_task = check_toxicity(normalized_message)
        semantic_task = check_semantic_intent(normalized_message)
        
        # Gather results concurrently
        toxicity_passed, semantic_passed = await asyncio.gather(toxicity_task, semantic_task)
        
        if not toxicity_passed:
            return await block_and_return("Toxic content detected", "TOXICITY_GUARD")
        await log_pipeline_event(request_id, "TOXICITY_GUARD", "PASSED")
        
        if not semantic_passed:
            return await block_and_return("Malicious intent detected", "SEMANTIC_GUARD")
        await log_pipeline_event(request_id, "SEMANTIC_GUARD", "PASSED")
    except Exception as e:
        print(f"PIPELINE CRITICAL ERROR: {str(e)}")
        return await block_and_return(f"Internal security check failed: {str(e)}", "SYSTEM")
    
    # PII Redaction
    safe_message = scrub_pii(normalized_message)
    if safe_message != normalized_message:
        await log_pipeline_event(request_id, "PII_GUARD", "REDACTED", {"original": normalized_message, "redacted": safe_message})
    else:
        await log_pipeline_event(request_id, "PII_GUARD", "PASSED")
    
    # LLM Generation (Now async)
    try:
        llm_output = await generate_response(safe_message)
        final_response = scrub_pii(llm_output.answer) 
        
        # --- NEW: GUARDRAILS INTEGRATION ---
        final_response = await apply_guardrails(final_response)
        # -----------------------------------
        
        await log_pipeline_event(request_id, "LLM_RESPONSE", "SUCCESS")

        # Finalize Audit Log
        latency = (datetime.utcnow() - start_time).total_seconds() * 1000
        await finalize_audit_log(request_id, "PASSED", int(latency))

        system_msg = {"user_email": current_user["email"], "role": "system", "content": final_response, "status": "PASSED", "timestamp": datetime.utcnow()}
        await chat_db.insert_one(system_msg.copy())
        
        # --- NEW: SIMPLE LOGGING ---
        risk_score = 0.0 if getattr(llm_output, 'is_safe', True) else 1.0 
        simple_langsmith_logger(message, risk_score, "ALLOW", final_response)
        # ---------------------------
        
        return {
            "status": "PASSED", 
            "original_message": message,
            "response": final_response,
            "is_safe_check": llm_output.is_safe
        }
    except Exception as e:
        print(f"LLM GENERATION ERROR: {str(e)}")
        return await block_and_return(f"LLM failed to generate response: {str(e)}", "LLM_ENGINE")

# 5. Telemetry Endpoints (Admin RBAC)
def mask_text(text: str) -> str:
    if not text or not isinstance(text, str): return text
    words = text.split()
    masked_words = []
    for w in words:
        if len(w) <= 2:
            masked_words.append(w[0] + "*" * (len(w)-1))
        else:
            masked_words.append(w[0] + "*" * (len(w)-2) + w[-1])
    return " ".join(masked_words)

@app.get("/logs")
async def get_logs(current_user: dict = Depends(require_any_admin)):
    db = client["SSA_Security"]
    query = {}
    is_super = current_user["role"] == "Super Admin"
    
    # Filter by department if not Super Admin
    if not is_super:
        query["user_context.department"] = current_user["department"]
        
    cursor = db["logs"].find(query).sort("timestamp", -1)
    logs = await cursor.to_list(length=50)
    
    for l in logs:
        l["id"] = str(l.pop("_id"))
        
        # Backward compatibility for current frontend mapping
        # We find the 'defining' event in the pipeline
        events = l.get("pipeline_events", [])
        
        # Default fallback values
        l["event"] = "SUCCESS" if l.get("final_status") == "PASSED" else "BLOCKED_SYSTEM"
        l["details"] = {"message": "Audit trace available", "response": "N/A"}
        
        for ev in events:
            if ev.get("status") == "BLOCKED":
                l["event"] = f"BLOCKED_{ev.get('layer')}"
                l["details"] = ev.get("details", {})
                break
            elif ev.get("layer") == "PII_GUARD" and ev.get("status") == "REDACTED":
                l["event"] = "PII_REDACTED"
                l["details"] = ev.get("details", {})
            elif ev.get("layer") == "LLM_RESPONSE":
                l["details"]["response"] = "Response generated"

        # Mask sensitive details for Department Admins
        if not is_super:
            details = l.get("details", {})
            for key in ["message", "original", "redacted", "response"]:
                if key in details:
                    details[key] = mask_text(details[key])
    
    return {"status": "success", "logs": logs, "viewer_scope": "Global" if is_super else current_user["department"]}

@app.get("/metrics")
async def get_metrics(current_user: dict = Depends(require_any_admin)):
    from collections import defaultdict
    from datetime import datetime, timedelta
    db = client["SSA_Security"]
    
    is_super = current_user["role"] == "Super Admin"
    query = {} if is_super else {"user_context.department": current_user["department"]}

    total = await db["logs"].count_documents(query)
    blocked = await db["logs"].count_documents({**query, "final_status": "BLOCKED"})
    safe = total - blocked
    
    # Chart Data
    cursor = db["logs"].find(query).sort("timestamp", 1).limit(1000)
    logs = await cursor.to_list(length=1000)
    
    grouped = {}
    now = datetime.utcnow()
    for i in range(11, -1, -1):
        h_obj = now - timedelta(hours=i)
        iso_key = h_obj.strftime("%Y-%m-%dT%H:00:00Z")
        grouped[iso_key] = {"safe": 0, "blocked": 0}

    for l in logs:
        ts = l.get("timestamp")
        if not ts: continue
        try:
            date_obj = ts if isinstance(ts, datetime) else datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            iso_key = date_obj.strftime("%Y-%m-%dT%H:00:00Z")
        except: continue
        if iso_key in grouped:
            if l.get("final_status") == "BLOCKED":
                grouped[iso_key]["blocked"] += 1
            else:
                grouped[iso_key]["safe"] += 1

    chart_data = [{"time": k, "safe": v["safe"], "blocked": v["blocked"]} for k,v in grouped.items()]
    
    # Recent Activity Map (using pipeline events)
    recent_cursor = db["logs"].find(query).sort("timestamp", -1).limit(4)
    recent_logs = await recent_cursor.to_list(length=4)
    recent_activity = []
    
    for r in recent_logs:
        ts = r.get("timestamp")
        time_str = ts.strftime("%H:%M") if isinstance(ts, datetime) else "Unknown Time"
        
        status = r.get("final_status", "UNKNOWN")
        detail_msg = "Request Processed"
        layer = "Security Pipeline"
        is_alert = False
        
        if status == "BLOCKED":
            is_alert = True
            # Find which layer blocked it
            for ev in r.get("pipeline_events", []):
                if ev.get("status") == "BLOCKED":
                    layer = ev.get("layer").replace("_", " ").title()
                    detail_msg = f"{layer} Intercepted Threat"
                    break
        else:
            # Check for PII Redaction in pipeline
            for ev in r.get("pipeline_events", []):
                if ev.get("layer") == "PII_GUARD" and ev.get("status") == "REDACTED":
                    layer = "PII Engine"
                    detail_msg = "Sensitive Data Scrubbed"
                    break

        recent_activity.append({
            "id": str(r["_id"]),
            "time": time_str,
            "message": detail_msg,
            "layer": layer,
            "isAlert": is_alert
        })
        
    return {
        "status": "success",
        "total": total,
        "safe": safe,
        "blocked": blocked,
        "viewer_scope": "Global" if is_super else current_user["department"],
        "chartData": chart_data,
        "recentActivity": recent_activity
    }

# 6. Entry Point
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)