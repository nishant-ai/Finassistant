"""
MongoDB Database Configuration and Connection
"""

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# MongoDB connection settings
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "financial_assistant")

# Global database client
_client: Optional[AsyncIOMotorClient] = None
_db = None


async def connect_to_mongo():
    """Initialize MongoDB connection"""
    global _client, _db

    try:
        # Configure connection options based on URL
        # For local MongoDB (mongodb://localhost), don't use TLS
        # For remote/cloud MongoDB (mongodb+srv://), use TLS
        connection_options = {
            'serverSelectionTimeoutMS': 5000,
            'connectTimeoutMS': 10000,
        }

        # Handle SSL/TLS for remote connections (MongoDB Atlas)
        if MONGODB_URL.startswith('mongodb+srv://') or ('mongodb.net' in MONGODB_URL):
            # For MongoDB Atlas, just enable TLS and let pymongo handle the rest
            # This works better with Python 3.12's stricter SSL defaults
            connection_options['tls'] = True
            logger.info("Using TLS for remote MongoDB connection")
        else:
            logger.info("Connecting to local MongoDB without TLS")

        _client = AsyncIOMotorClient(MONGODB_URL, **connection_options)
        _db = _client[DATABASE_NAME]

        # Test the connection
        await _client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB")

        # Create indexes
        await create_indexes()

    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close MongoDB connection"""
    global _client

    if _client:
        _client.close()
        logger.info("MongoDB connection closed")


async def create_indexes():
    """Create database indexes for better query performance"""
    try:
        # Index for chat sessions
        await _db.chat_sessions.create_index([("created_at", -1)])
        await _db.chat_sessions.create_index([("user_id", 1)])

        # Index for messages
        await _db.messages.create_index([("session_id", 1), ("created_at", 1)])

        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")


def get_database():
    """Get database instance"""
    return _db


def get_collection(collection_name: str):
    """Get a specific collection"""
    if _db is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return _db[collection_name]