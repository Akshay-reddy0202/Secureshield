import asyncio
import motor.motor_asyncio
client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://localhost:27017')
db = client['SSA_Security']
async def main():
    users = await db['users'].find().to_list(10)
    for u in users:
        print(f"Role: {u.get('role')}, Dept: {u.get('department')}")
asyncio.run(main())
