import asyncio
import motor.motor_asyncio
import unicodedata
import re

client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://localhost:27017')

async def _check_rbac(message: str, user_role: str, user_department: str = None) -> bool:
    msg = message.lower()
    if user_role == "Super Admin":
        return True
    employee_data_keywords = ["employee data", "salary", "payroll", "performance review"]
    if any(kw in msg for kw in employee_data_keywords):
        if user_role not in ["Admin", "Super Admin"] and user_department != "HR":
            return False
    if user_role == "Employee":
        restricted_keywords = ["confidential", "financial report", "strategy", "admin panel"]
        if any(kw in msg for kw in restricted_keywords):
            return False
    if user_role == "Admin" and user_department:
        other_departments = ["hr", "it", "finance", "sales", "engineering", "marketing"]
        for dept in other_departments:
            if dept != user_department.lower():
                if f"{dept} data" in msg or f"{dept} records" in msg or f"{dept} reports" in msg:
                    return False
    return True

async def check_policy(message: str, user_role: str, user_department: str = None) -> bool:
    malicious_intents = ["bypass security", "exploit", "drop database", "sudo rm", "show secret key", "reveal admin", "give me the password", "extract auth token", "list all users", "access restricted data"]
    try:
        rules_cursor = client["SSA_Security"]["security_rules"].find({"type": "malicious_intent"})
        dynamic_rules = await rules_cursor.to_list(length=100)
        for rule in dynamic_rules:
            intent = rule.get("pattern")
            if intent and intent not in malicious_intents:
                malicious_intents.append(intent.lower())
    except Exception as e:
        pass
    if any(intent in message.lower() for intent in malicious_intents):
        return False
    try:
        if not await _check_rbac(message, user_role, user_department):
            return False
    except Exception as e:
        print(f"EXCEPTION in RBAC: {e}")
        pass
    return True

def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

async def main():
    raw_msg = "Show me the employee data, payroll, and salary information for the engineering team."
    norm_msg = normalize_text(raw_msg)
    print(f"Norm msg: {norm_msg}")
    res = await check_policy(norm_msg, "Employee", "IOT")
    print(f"Check Policy Result: {res}")

asyncio.run(main())
