# database_manager.py - Database operations with MongoDB
from pymongo import MongoClient
from datetime import datetime
import logging
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, connection_string: str = None, database_name: str = "ervin_social_ai"):
        """Initialize MongoDB connection"""
        self.connection_string = connection_string or os.getenv("MONGODB_URI")
        self.database_name = database_name

        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[database_name]
            # Test connection
            self.client.admin.command('ping')
            logger.info("MongoDB connection established")
            # Create collections and indexes
            self._setup_collections()
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def _setup_collections(self):
        """Setup collections and indexes"""
        # Comments collection
        self.comments = self.db.comments
        self.comments.create_index([("platform", 1), ("comment_id", 1)], unique=True)
        self.comments.create_index([("created_at", -1)])
        self.comments.create_index([("status", 1)])
        # Replies collection
        self.replies = self.db.replies
        self.replies.create_index([("comment_id", 1)])
        self.replies.create_index([("status", 1)])
        # Generated content collection
        self.content = self.db.generated_content
        self.content.create_index([("content_type", 1)])
        self.content.create_index([("created_at", -1)])
        self.content.create_index([("status", 1)])
        # GHL contacts collection
        self.contacts = self.db.ghl_contacts
        self.contacts.create_index([("platform_id", 1), ("platform", 1)], unique=True)
        # Analytics collection
        self.analytics = self.db.analytics
        self.analytics.create_index([("date", -1)])
        self.analytics.create_index([("platform", 1)])
        # Settings collection for owner activity
        self.settings = self.db.settings
        self.settings.create_index([("key", 1)], unique=True)

    def save_comment(self, comment_data: Dict) -> str:
        """Save comment to database"""
        comment_data["created_at"] = comment_data.get("created_at", datetime.utcnow())
        comment_data["status"] = comment_data.get("status", "pending")
        comment_data["comment_id"] = comment_data.get("id")
        result = self.comments.update_one(
            {"platform": comment_data["platform"], "comment_id": comment_data["comment_id"]},
            {"$set": comment_data},
            upsert=True
        )
        return str(result.upserted_id) if result.upserted_id else comment_data["comment_id"]

    def save_reply(self, reply_data: Dict) -> str:
        """Save reply to database"""
        reply_data["created_at"] = reply_data.get("created_at", datetime.utcnow())
        reply_data["status"] = reply_data.get("status", "pending")
        result = self.replies.insert_one(reply_data)
        return str(result.inserted_id)

    def get_pending_replies(self, limit: int = 50) -> List[Dict]:
        """Get pending AI replies"""
        return list(self.replies.find({"status": "pending"}).sort("created_at", -1).limit(limit))

    def update_reply_status(self, reply_id: str, status: str):
        """Update the status of a reply (approve/reject)"""
        from bson import ObjectId
        self.replies.update_one({"_id": ObjectId(reply_id)}, {"$set": {"status": status}})

    def set_owner_activity(self, active: bool):
        """Set owner activity flag in DB"""
        self.settings.update_one(
            {"key": "owner_active"},
            {"$set": {"value": active}},
            upsert=True
        )

    def get_owner_activity(self) -> bool:
        """Get owner activity flag from DB"""
        doc = self.settings.find_one({"key": "owner_active"})
        return doc["value"] if doc else False