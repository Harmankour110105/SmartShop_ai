# backend/db.py

import motor.motor_asyncio
import logging
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection details
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "smartshop"

# Global database client
client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None

class User(BaseModel):
    username: str
    hashed_password: str

    @classmethod
    async def find_one(cls, query: dict):
        """Find a single user by query"""
        global db
        if db is None:
            await connect_to_db()
        user_dict = await db.users.find_one(query)
        if user_dict:
            return cls(**user_dict)
        return None

    async def insert(self):
        """Insert a new user"""
        global db
        if db is None:
            await connect_to_db()
        user_dict = self.dict()
        await db.users.insert_one(user_dict)

async def connect_to_db():
    """Initialize database connection"""
    global client, db
    try:
        # Create client
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        # Create indexes
        await db.users.create_index("username", unique=True)
        await db.cart.create_index([("username", 1), ("item.product", 1)], unique=True)
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise e

async def close_db_connection():
    """Close database connection"""
    global client
    if client:
        client.close()

async def get_database() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    """Get database instance"""
    global db
    if db is None:
        await connect_to_db()
    return db
