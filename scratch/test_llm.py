import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.append('.')

from app.services.llm_service import generate_response

def test():
    print("Testing LLM Response Generation...")
    try:
        res = generate_response("Hello, what is SecureShield?")
        print(f"LLM Response: {res.answer}")
        print(f"Is Safe: {res.is_safe}")
    except Exception as e:
        print(f"CRITICAL ERROR in LLM Service: {str(e)}")

if __name__ == "__main__":
    test()
