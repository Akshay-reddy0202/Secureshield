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
    # Query 'chats' collection which is used by the main application
    msgs = await db['chats'].find().sort('_id', -1).to_list(10)
    for m in msgs:
        print(f"User: {m.get('user_email')} | Role: {m.get('role')} | Content: {m.get('content')}")

asyncio.run(main())

