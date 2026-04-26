from app.services.logger import client

async def check_policy(message: str, user_role: str) -> bool:
    # 1. Fallback Intents
    malicious_intents = [
        "bypass security", "exploit", "drop database", "sudo rm",
        "show secret key", "reveal admin", "give me the password",
        "extract auth token", "list all users", "access restricted data"
    ]
    
    # 2. Dynamic Intents from MongoDB
    try:
        rules_cursor = client["SSA_Security"]["security_rules"].find({"type": "malicious_intent"})
        dynamic_rules = await rules_cursor.to_list(length=100)
        for rule in dynamic_rules:
            intent = rule.get("pattern")
            if intent and intent not in malicious_intents:
                malicious_intents.append(intent.lower())
    except Exception as e:
        print(f"⚠️ Could not load dynamic policies: {str(e)}")
    
    if any(intent in message.lower() for intent in malicious_intents):
        return False
        
    return True
