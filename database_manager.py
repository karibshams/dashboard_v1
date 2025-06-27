import psycopg2
from psycopg2 import sql
import logging
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, connection_string: str = None, database_name: str = "karibvaiengageflowai"):
        """Initialize PostgreSQL connection"""
        self.connection_string = connection_string or os.getenv("POSTGRES_URL")
        self.database_name = database_name

        try:
            # Establish PostgreSQL connection
            self.connection = psycopg2.connect(self.connection_string)
            self.cursor = self.connection.cursor()
            logger.info("PostgreSQL connection established")
            # Create tables if they don't exist
            self._setup_tables()
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def _setup_tables(self):
        """Setup tables for comments, replies, content, and settings"""
        try:
            # Create comments table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    comment_id SERIAL PRIMARY KEY,
                    platform VARCHAR(255) NOT NULL,
                    text TEXT,
                    author VARCHAR(255),
                    status VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create replies table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS replies (
                    reply_id SERIAL PRIMARY KEY,
                    comment_id INTEGER REFERENCES comments(comment_id),
                    reply TEXT,
                    status VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create generated content table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS generated_content (
                    content_id SERIAL PRIMARY KEY,
                    content_type VARCHAR(255),
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Create settings table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    setting_key VARCHAR(255) PRIMARY KEY,
                    setting_value TEXT
                );
            """)
            
            # Commit the changes
            self.connection.commit()
            logger.info("Tables created successfully")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Failed to setup tables: {e}")
            raise

    def save_comment(self, comment_data: Dict) -> str:
        """Save comment to database"""
        try:
            insert_query = """
                INSERT INTO comments (platform, text, author, status)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (comment_id) DO UPDATE
                SET platform = EXCLUDED.platform, text = EXCLUDED.text, author = EXCLUDED.author, status = EXCLUDED.status;
            """
            self.cursor.execute(insert_query, (
                comment_data["platform"], comment_data["text"], comment_data["author"], comment_data["status"]
            ))
            self.connection.commit()
            logger.info(f"Comment saved: {comment_data['comment_id']}")
            return str(comment_data["comment_id"])
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error saving comment: {e}")
            raise

    def save_reply(self, reply_data: Dict) -> str:
        """Save reply to database"""
        try:
            insert_query = """
                INSERT INTO replies (comment_id, reply, status)
                VALUES (%s, %s, %s)
                RETURNING reply_id;
            """
            self.cursor.execute(insert_query, (
                reply_data["comment_id"], reply_data["reply"], reply_data["status"]
            ))
            self.connection.commit()
            reply_id = self.cursor.fetchone()[0]
            logger.info(f"Reply saved: {reply_id}")
            return str(reply_id)
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error saving reply: {e}")
            raise

    def get_pending_replies(self, limit: int = 50) -> List[Dict]:
        """Get pending AI replies"""
        try:
            select_query = """
                SELECT reply_id, comment_id, reply, status FROM replies WHERE status = 'pending' LIMIT %s;
            """
            self.cursor.execute(select_query, (limit,))
            rows = self.cursor.fetchall()
            replies = [{"reply_id": row[0], "comment_id": row[1], "reply": row[2], "status": row[3]} for row in rows]
            return replies
        except Exception as e:
            logger.error(f"Error fetching pending replies: {e}")
            raise

    def update_reply_status(self, reply_id: str, status: str):
        """Update the status of a reply (approve/reject)"""
        try:
            update_query = """
                UPDATE replies SET status = %s WHERE reply_id = %s;
            """
            self.cursor.execute(update_query, (status, reply_id))
            self.connection.commit()
            logger.info(f"Reply status updated: {reply_id}")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error updating reply status: {e}")
            raise

    def set_owner_activity(self, active: bool):
        """Set owner activity flag in DB"""
        try:
            upsert_query = """
                INSERT INTO settings (setting_key, setting_value)
                VALUES (%s, %s)
                ON CONFLICT (setting_key) DO UPDATE SET setting_value = EXCLUDED.setting_value;
            """
            self.cursor.execute(upsert_query, ("owner_active", str(active)))
            self.connection.commit()
            logger.info(f"Owner activity set to: {active}")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error updating owner activity: {e}")
            raise

    def get_owner_activity(self) -> bool:
        """Get owner activity flag from DB"""
        try:
            select_query = """
                SELECT setting_value FROM settings WHERE setting_key = %s;
            """
            self.cursor.execute(select_query, ("owner_active",))
            result = self.cursor.fetchone()
            return result[0] == "True" if result else False
        except Exception as e:
            logger.error(f"Error fetching owner activity: {e}")
            raise
