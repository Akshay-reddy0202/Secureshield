import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="instructor.providers.gemini")

from fastapi import FastAPI, Query, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
# Force Uvicorn Reload for Policy Engine updates
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
        with open("../logs/simple_audit.log", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Logging error: {e}")

import re

async def apply_guardrails(response_text: str) -> str:
    """Apply Guardrails after LLM response. Fail-safe."""
    original_text = response_text
    try:
        patterns = {
            "JWT_TOKEN": r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+",
            "API_KEY": r"sk-[a-zA-Z0-9]{20,}",
            "AWS_KEY": r"AKIA[0-9A-Z]{16}",
            "GENERIC_SECRET": r"(?i)(?:api_key|apikey|access_token|secret_key)[=:\s]+['\"]?([a-zA-Z0-9\-_]{32,})['\"]?"
        }
        
        redacted_text = original_text
        total_findings = 0
        
        for secret_type, pattern in patterns.items():
            matches = list(re.finditer(pattern, original_text))
            if matches:
                total_findings += len(matches)
                for match in matches:
                    if match.lastindex and match.lastindex >= 1:
                        # Replace the captured group
                        redacted_text = redacted_text.replace(match.group(1), f"[REDACTED_{secret_type}]")
                    else:
                        redacted_text = redacted_text.replace(match.group(0), f"[REDACTED_{secret_type}]")
                
        # Block only if severe (e.g. 3 or more secrets leaked)
        if total_findings >= 3:
            raise ValueError(f"Severe output violation: {total_findings} secrets detected")
            
        return redacted_text
    except ValueError as ve:
        # Re-raise so the pipeline can catch and block it
        raise ve
    except Exception as e:
        print(f"Guardrails error: {e}")
        return original_text # Fallback: return original output
# ---------------------------------

# 1. Initialize App
app = FastAPI(title=settings.app_name)

chat_db = client["SSA_Security"]["chats"]

# 2. Add CORS Middleware (Crucial for Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "https://secureshield-rho-two.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- NEW: NETWORK GUARD (RATE LIMITING) ---
import time

NETWORK_RATE_LIMIT_COUNT = 30
NETWORK_RATE_LIMIT_WINDOW_SECONDS = 60
ip_request_counts = {}

@app.middleware("http")
async def network_guard_middleware(request: Request, call_next):
    try:
        path = request.url.path
        if path == "/" or path.startswith("/health"):
            return await call_next(request)
            
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        if client_ip not in ip_request_counts:
            ip_request_counts[client_ip] = []
            
        # Clean up old requests
        ip_request_counts[client_ip] = [
            t for t in ip_request_counts[client_ip] 
            if current_time - t < NETWORK_RATE_LIMIT_WINDOW_SECONDS
        ]
        
        if len(ip_request_counts[client_ip]) >= NETWORK_RATE_LIMIT_COUNT:
            return JSONResponse(
                status_code=200,
                content={"status": "BLOCKED", "reason": "Too many requests detected"}
            )
            
        ip_request_counts[client_ip].append(current_time)
        return await call_next(request)
        
    except Exception as e:
        print(f"Network Guard Error: {e}")
        return await call_next(request)
# ------------------------------------------

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

from app.services.logger import audit_collection
from app.services.attack_analyzer import analyze_attack

async def _append_attack_analysis(request_id: str, current_user: dict, response: dict, client_ip: str = None) -> dict:
    try:
        doc = await audit_collection.find_one({"request_id": request_id})
        pipeline_events = doc.get("pipeline_events", []) if doc else []
        analysis = analyze_attack(pipeline_events, user_email=current_user.get("email"), ip_address=client_ip)
        if analysis:
            response["attack_analysis"] = analysis
            await audit_collection.update_one(
                {"request_id": request_id},
                {"$set": {
                    "attack_type": analysis.get("attack_type"),
                    "entry_point": analysis.get("entry_point"),
                    "risk_level": analysis.get("risk_level"),
                    "root_cause": analysis.get("root_cause")
                }}
            )
    except Exception as e:
        print(f"Attack Analyzer Failed: {e}")
    return response

@app.post("/chat")
async def chat_endpoint(request: Request, data: ChatMessageModel, current_user: dict = Depends(get_current_user)):
    start_time = datetime.utcnow()
    request_id = str(uuid.uuid4())
    message = data.message
    role = current_user["role"]
    client_ip = request.client.host if hasattr(request, "client") and request.client else "unknown"
    
    # 1. Initialize the audit trail for this request
    await init_audit_log(request_id, current_user, ip_address=client_ip)

    # Save User Context in chat history
    await chat_db.insert_one({"user_email": current_user["email"], "role": "user", "content": message, "timestamp": datetime.utcnow()})
    
    normalized_message = normalize_text(message)
    
    async def block_and_return(reason, layer):
        # Log the block in the pipeline
        await log_pipeline_event(request_id, layer, "BLOCKED", {"reason": reason, "message": normalized_message})
        
        # Finalize the log
        latency = (datetime.utcnow() - start_time).total_seconds() * 1000
        await finalize_audit_log(request_id, "BLOCKED", int(latency))
        
        system_msg = {"user_email": current_user["email"], "role": "system", "content": f"🛡️ BLOCKED: {reason}", "status": "BLOCKED", "reason": reason, "timestamp": datetime.utcnow()}
        await chat_db.insert_one(system_msg.copy())
        
        # --- NEW: SIMPLE LOGGING ---
        simple_langsmith_logger(message, 1.0, "BLOCK", f"Blocked by {layer}: {reason}")
        # ---------------------------
        
        response = {"status": "BLOCKED", "reason": reason}
        return await _append_attack_analysis(request_id, current_user, response, client_ip)

    # Pipeline Checks
    import asyncio
    
    if not await check_input(normalized_message): 
        return await block_and_return("Forbidden pattern detected (Static Input Guard)", "INPUT_GUARD")
    await log_pipeline_event(request_id, "INPUT_GUARD", "PASSED")
    
    if not await check_policy(normalized_message, role, current_user.get("department")): 
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
        
        response = {
            "status": "PASSED", 
            "original_message": message,
            "response": final_response,
            "is_safe_check": llm_output.is_safe
        }
        return await _append_attack_analysis(request_id, current_user, response, client_ip)
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
    
    # Chart Data & Stats
    cursor = db["logs"].find(query).sort("timestamp", 1).limit(1000)
    logs = await cursor.to_list(length=1000)
    
    grouped = {}
    now = datetime.utcnow()
    for i in range(11, -1, -1):
        h_obj = now - timedelta(hours=i)
        iso_key = h_obj.strftime("%Y-%m-%dT%H:00:00Z")
        grouped[iso_key] = {"safe": 0, "blocked": 0}

    risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    attack_trends = defaultdict(int)
    layer_stats = defaultdict(int)

    for l in logs:
        ts = l.get("timestamp")
        if not ts: continue
        
        # New Stats Processing
        risk = l.get("risk_level")
        if risk in risk_distribution:
            risk_distribution[risk] += 1
            
        attack = l.get("attack_type")
        if attack:
            attack_trends[attack] += 1
            
        for ev in l.get("pipeline_events", []):
            layer = ev.get("layer")
            if layer:
                layer_stats[layer] += 1

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
    attack_trends_list = [{"name": k, "value": v} for k, v in attack_trends.items()]
    layer_stats_list = [{"name": k, "value": v} for k, v in layer_stats.items()]
    
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
        "recentActivity": recent_activity,
        "riskDistribution": risk_distribution,
        "attackTrends": attack_trends_list,
        "layerStats": layer_stats_list
    }

# 6. Entry Point
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
