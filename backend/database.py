import os
import certifi
import logging
from typing import Optional
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

load_dotenv()

logger = logging.getLogger("database")

MONGODB_URI = os.getenv("MONGODB_URI")
DEFAULT_DB_NAME = os.getenv("MONGODB_DB_NAME", "optimatrix_chat")

_mongo_client: Optional[MongoClient] = None
_db: Optional[Database] = None

def get_mongo_client() -> Optional[MongoClient]:
    global _mongo_client
    if _mongo_client is None and MONGODB_URI:
        # Strategy 1: Standard client with certifi CA bundle
        try:
            client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            _mongo_client = client
            logger.info("MongoDB client connected successfully using certifi CA bundle.")
            return _mongo_client
        except Exception as e1:
            logger.warning(f"MongoDB connection attempt with certifi failed: {e1}. Trying TLS fallback...")
        
        # Strategy 2: Fallback with tlsAllowInvalidCertificates (fixes Render/OpenSSL TLS handshake alerts)
        try:
            client = MongoClient(MONGODB_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            _mongo_client = client
            logger.info("MongoDB client connected successfully using fallback TLS configuration.")
            return _mongo_client
        except Exception as e2:
            logger.error(f"Failed to connect to MongoDB: {e2}")
            _mongo_client = None

    return _mongo_client

def get_database() -> Optional[Database]:
    global _db
    if _db is not None:
        return _db
    
    client = get_mongo_client()
    if client is not None:
        try:
            db_instance = client.get_database()
            if not db_instance.name:
                db_instance = client.get_database(DEFAULT_DB_NAME)
            _db = db_instance
        except Exception:
            _db = client.get_database(DEFAULT_DB_NAME)
        
        # Ensure collection indexes
        try:
            init_indexes(_db)
        except Exception as e:
            logger.warning(f"Error initializing indexes: {e}")
            
    return _db

def init_indexes(database: Database):
    """Ensure required indexes for performance and data lifecycle."""
    if database is None:
        return
        
    try:
        # Sessions TTL index (24 hours)
        sessions_coll = database["chat_sessions"]
        sessions_coll.create_index("updated_at", expireAfterSeconds=86400)
        sessions_coll.create_index("session_id", unique=True)
    except Exception as e:
        logger.warning(f"Session index creation: {e}")
    
    try:
        # Inquiries index for fast querying by date and contact number
        inquiries_coll = database["inquiries"]
        inquiries_coll.create_index("createdAt")
        inquiries_coll.create_index("contactNumber")
        logger.info("MongoDB indexes verified for 'chat_sessions' and 'inquiries'.")
    except Exception as e:
        logger.warning(f"Inquiries index creation: {e}")

def get_inquiries_collection() -> Optional[Collection]:
    db = get_database()
    if db is not None:
        return db["inquiries"]
    return None

def get_sessions_collection() -> Optional[Collection]:
    db = get_database()
    if db is not None:
        return db["chat_sessions"]
    return None
