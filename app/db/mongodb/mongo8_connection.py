from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config_core import settings

client = AsyncIOMotorClient(settings.MONGODB_URL)

async def get_mongodb():
    return client
