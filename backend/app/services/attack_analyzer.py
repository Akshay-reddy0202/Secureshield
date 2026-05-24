import time

# In-memory store for attack correlation
_attack_history = {}
_ATTACK_THRESHOLD = 3
_ATTACK_WINDOW_SECONDS = 3600

def _check_attack_threshold(identifier: str) -> bool:
    """Helper to track repeated attacks per user/IP in-memory."""
    if not identifier:
        return False
    current_time = time.time()
    if identifier not in _attack_history:
        _attack_history[identifier] = []
    
    # Clean old records
    _attack_history[identifier] = [
        t for t in _attack_history[identifier] 
        if current_time - t < _ATTACK_WINDOW_SECONDS
    ]
    _attack_history[identifier].append(current_time)
    return len(_attack_history[identifier]) >= _ATTACK_THRESHOLD

def analyze_attack(pipeline_events: list, user_email: str = None, ip_address: str = None) -> dict:
    """
    Analyzes pipeline events to determine attack characteristics.
    Does not depend on MongoDB. Accepts simple Python inputs.
    """
    result = {
        "attack_type": "Unknown",
        "entry_point": "N/A",
        "layers_triggered": [],
        "risk_level": "LOW",
        "root_cause": "N/A",
        "suggested_fix": "",
        "threat_level": "NORMAL"
    }

    if not pipeline_events:
        return result

    flagged_events = []
    for event in pipeline_events:
        # Check for flagged/blocked status
        status = str(event.get("status", "")).upper()
        if status in ("FLAGGED", "BLOCKED", "FAILED", "SUSPICIOUS", "DENIED", "REJECTED"):
            flagged_events.append(event)
            
    if not flagged_events:
        # If no explicit status, maybe the presence in events means it was triggered?
        # But instructions say "entry_point = first flagged layer", implying we look for flagged ones.
        return result

    # Entry point is the first flagged layer
    entry_point = flagged_events[0].get("layer", "UNKNOWN")
    result["entry_point"] = entry_point

    # Layers triggered: unique layers from flagged events
    layers_triggered = []
    for event in flagged_events:
        layer = event.get("layer", "UNKNOWN")
        if layer not in layers_triggered:
            layers_triggered.append(layer)
    
    result["layers_triggered"] = layers_triggered

    # Detect attack type from reasons
    reasons = []
    for event in flagged_events:
        details = event.get("details", {})
        if isinstance(details, dict) and "reason" in details:
            reasons.append(str(details["reason"]).lower())
        elif "reason" in event: # Just in case it's flat
            reasons.append(str(event["reason"]).lower())

    combined_reasons = " ".join(reasons)

    # Simple heuristic for attack type from reasons
    if any(keyword in combined_reasons for keyword in ["sql", "injection", "sqli"]):
        result["attack_type"] = "SQL Injection"
        result["suggested_fix"] = "Sanitize user inputs and use parameterized queries"
    elif any(keyword in combined_reasons for keyword in ["xss", "cross-site", "script"]):
        result["attack_type"] = "Cross-Site Scripting (XSS)"
        result["suggested_fix"] = "Escape user input before rendering and implement CSP"
    elif any(keyword in combined_reasons for keyword in ["brute", "force", "credential", "password"]):
        result["attack_type"] = "Brute Force / Credential Stuffing"
        result["suggested_fix"] = "Implement rate limiting and account lockout policies"
    elif any(keyword in combined_reasons for keyword in ["ddos", "rate", "limit", "flood"]):
        result["attack_type"] = "DDoS / Rate Limit Exceeded"
        result["suggested_fix"] = "Increase rate limiting strictness and deploy WAF rules"
    elif any(keyword in combined_reasons for keyword in ["bot", "scraper", "crawler", "automation"]):
        result["attack_type"] = "Malicious Bot Activity"
        result["suggested_fix"] = "Implement CAPTCHA and advanced bot protection"
    elif any(keyword in combined_reasons for keyword in ["semantic", "prompt", "jailbreak", "ignore previous"]):
        result["attack_type"] = "Prompt Injection / Semantic Attack"
        result["suggested_fix"] = "Enhance prompt filtering and implement strict boundaries"
    elif any(keyword in combined_reasons for keyword in ["data extraction", "exfiltrate", "dump", "steal"]):
        result["attack_type"] = "Data Extraction"
        result["suggested_fix"] = "Implement strict data access controls and DLP policies"
    elif any(keyword in combined_reasons for keyword in ["toxic", "hate", "harassment", "profanity"]):
        result["attack_type"] = "Toxicity / Content Violation"
        result["suggested_fix"] = "Update toxicity filters and moderation guidelines"
    else:
        if combined_reasons:
            result["attack_type"] = "Suspicious Payload"
            result["suggested_fix"] = "Review specific layer logs for exact vulnerability"
        else:
            result["attack_type"] = "Unknown Attack"
            result["suggested_fix"] = "Investigate flagged layer manually"

    # Risk level: 1 -> LOW, 2 -> MEDIUM, 3+ -> HIGH
    num_layers = len(layers_triggered)
    if num_layers >= 3:
        result["risk_level"] = "HIGH"
        result["threat_level"] = "CRITICAL"
    elif num_layers == 2:
        result["risk_level"] = "MEDIUM"
        result["threat_level"] = "ELEVATED"
    elif num_layers == 1:
        result["risk_level"] = "LOW"
        result["threat_level"] = "NORMAL"

    # Increase severity for: prompt injection, data extraction
    is_high_severity_attack = (
        "prompt injection" in result["attack_type"].lower() or 
        "data extraction" in result["attack_type"].lower() or
        any(k in combined_reasons for k in ["prompt injection", "data extraction"])
    )
    
    if is_high_severity_attack:
        if result["risk_level"] == "LOW":
            result["risk_level"] = "MEDIUM"
            result["threat_level"] = "ELEVATED"
        elif result["risk_level"] == "MEDIUM":
            result["risk_level"] = "HIGH"
            result["threat_level"] = "CRITICAL"
        elif result["risk_level"] == "HIGH":
            result["risk_level"] = "CRITICAL"
            result["threat_level"] = "SEVERE"

    # Root Cause Analysis: Map failures of earlier passed layers
    passed_layers = []
    
    # Since Network Guard is a middleware, if pipeline_events exist, it means Network Guard passed.
    if pipeline_events and "NETWORK" not in str(pipeline_events[0].get("layer", "")).upper():
        passed_layers.append("NETWORK_GUARD")
        
    for event in pipeline_events:
        status = str(event.get("status", "")).upper()
        if status in ("FLAGGED", "BLOCKED", "FAILED", "SUSPICIOUS", "DENIED", "REJECTED"):
            break
        layer = str(event.get("layer", "UNKNOWN")).upper()
        if layer not in passed_layers:
            passed_layers.append(layer)

    mapped_failures = []
    for layer in passed_layers:
        if "NETWORK" in layer:
            mapped_failures.append("missing rate limiting")
        elif "INPUT" in layer:
            mapped_failures.append("weak input validation")
        elif "POLICY" in layer:
            mapped_failures.append("weak RBAC")

    if mapped_failures:
        result["root_cause"] = "Bypassed earlier defenses due to: " + ", ".join(mapped_failures)
    else:
        result["root_cause"] = "N/A"

    # Attack Correlation check
    try:
        threshold_exceeded = False
        if flagged_events:
            if user_email and _check_attack_threshold(f"user:{user_email}"):
                threshold_exceeded = True
            if ip_address and _check_attack_threshold(f"ip:{ip_address}"):
                threshold_exceeded = True
                
        if threshold_exceeded:
            result["threat_level"] = "HIGH"
        elif flagged_events and result["threat_level"] == "NORMAL":
            result["threat_level"] = "SUSPICIOUS"
    except Exception as e:
        print(f"Attack correlation tracking failed: {e}")
        result["threat_level"] = "NORMAL"

    return result
