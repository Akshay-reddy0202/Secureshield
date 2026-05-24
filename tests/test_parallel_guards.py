import asyncio
import time
import os
from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.append('.')

from app.layers.toxicity_guard import check_toxicity
from app.layers.semantic_guard import check_semantic_intent

async def test_parallel():
    print("Testing PARALLEL Guard Execution...")
    start = time.time()
    
    # Run in parallel
    results = await asyncio.gather(
        check_toxicity("Hello world"),
        check_semantic_intent("Hello world")
    )
    
    end = time.time()
    print(f"Results: {results}")
    print(f"Total time for 2 guards: {end - start:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(test_parallel())
