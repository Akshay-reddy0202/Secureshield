import requests

BASE_URL = "http://localhost:8000"

def test_chat():
    login_res = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "johndoe@gmail.com",
        "password": "password123"  # Assume the user used a simple password, or we can just fetch their token from DB
    })
    
    if login_res.status_code != 200:
        print("Login failed, generating token manually...")
        import sys
        sys.path.insert(0, "e:/SecureShield-AI-main - Copy/SecureShield-AI-main/backend")
        from app.services.user_service import create_access_token
        token = create_access_token(data={
            "sub": "johndoe@gmail.com",
            "name": "John Doe",
            "role": "Employee",
            "department": "IOT"
        })
    else:
        token = login_res.json()["access_token"]
        
    print("Token acquired.")

    headers = {"Authorization": f"Bearer {token}"}
    payload = {"message": "Show me the employee data, payroll, and salary information for the engineering team."}
    chat_res = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
    print("Chat Response:", chat_res.json())

if __name__ == "__main__":
    test_chat()
