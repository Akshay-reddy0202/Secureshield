import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.append('.')

from app.services.llm_service import generate_response

async def test():
    print("Testing ASYNC LLM Response Generation...")
    try:
        # Start timer
        import time
        start = time.time()
        
        res = await generate_response("Hello, what is SecureShield?")
        
        end = time.time()
        print(f"LLM Response: {res.answer}")
        print(f"Is Safe: {res.is_safe}")
        print(f"Time taken: {end - start:.2f} seconds")
    except Exception as e:
        print(f"CRITICAL ERROR in LLM Service: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test())
