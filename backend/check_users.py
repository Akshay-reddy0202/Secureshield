import os
import asyncio
import motor.motor_asyncio
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Fetch MongoDB URI or fallback to local
mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
print(f"Connecting to: {mongodb_uri.split('@')[-1] if '@' in mongodb_uri else mongodb_uri}")

client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_uri)
db = client['SSA_Security']

async def main():
    users = await db['users'].find().to_list(100)
    for u in users:
        print(f"{u.get('email')}: Role={u.get('role')}, Dept={u.get('department')}")

asyncio.run(main())

