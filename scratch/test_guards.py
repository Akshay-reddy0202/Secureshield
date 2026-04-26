import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.append('.')

from app.layers.toxicity_guard import check_toxicity
from app.layers.semantic_guard import check_semantic_intent

async def test():
    print("Testing Toxicity Guard...")
    res1 = await check_toxicity("Hello world")
    print(f"Toxicity Guard result for 'Hello world': {res1}")
    
    print("\nTesting Semantic Guard...")
    res2 = await check_semantic_intent("Hello world")
    print(f"Semantic Guard result for 'Hello world': {res2}")

if __name__ == "__main__":
    asyncio.run(test())
