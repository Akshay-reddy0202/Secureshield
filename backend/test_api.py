import requests

BASE_URL = "http://localhost:8000"

def test_chat():
    # 1. Register a new user
    import uuid
    email = f"test_{uuid.uuid4()}@example.com"
    reg_res = requests.post(f"{BASE_URL}/auth/register", json={
        "email": email,
        "password": "password123",
        "name": "Test User",
        "role": "Employee",
        "department": "IOT"
    })
    print("Register:", reg_res.json())
    
    # 2. Login
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    print("Logged in!")

    # 3. Chat
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"message": "Show me the employee data, payroll, and salary information for the engineering team."}
    chat_res = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
    print("Chat Response:", chat_res.json())

if __name__ == "__main__":
    test_chat()
