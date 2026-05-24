from app.services.logger import client

async def check_input(text: str) -> bool:
    # 1. Hardcoded Fallback Patterns (Static Defense)
    blocked_patterns = [
        "hack", "attack", "bypass", "ignore previous", "ignore instructions",
        "forget all previous", "system prompt", "developer mode", "jailbreak",
        "dan mode", "act as", "disregard instructions", "reveal secret"
    ]
    
    # 2. Dynamic Rules from MongoDB (Live Defense)
    try:
        rules_cursor = client["SSA_Security"]["security_rules"].find({"type": "blocked_pattern"})
        dynamic_rules = await rules_cursor.to_list(length=100)
        for rule in dynamic_rules:
            pattern = rule.get("pattern")
            if pattern and pattern not in blocked_patterns:
                blocked_patterns.append(pattern.lower())
    except Exception as e:
        print(f"⚠️ Could not load dynamic rules: {str(e)}")

    # 3. Perform Check
    for pattern in blocked_patterns:
        if pattern in text: 
            return False
    return True