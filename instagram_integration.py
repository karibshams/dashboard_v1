# instagram_integration.py - Instagram Business API integration
import requests
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class InstagramIntegrator:
    def __init__(self, access_token: str, instagram_business_account_id: str):
        """Initialize Instagram Business API client"""
        self.access_token = access_token
        self.account_id = instagram_business_account_id
        self.base_url = "https://graph.facebook.com/v18.0"
        
    def get_recent_media(self, limit: int = 25) -> List[Dict]:
        """Get recent Instagram media posts"""
        
        try:
            url = f"{self.base_url}/{self.account_id}/media"
            params = {
                "access_token": self.access_token,
                "limit": limit,
                "fields": "id,caption,media_type,media_url,permalink,timestamp,comments{id,text,username,timestamp,like_count}"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            media = data.get("data", [])
            
            logger.info(f"Retrieved {len(media)} Instagram media posts")
            return media
            
        except Exception as e:
            logger.error(f"Failed to get Instagram media: {e}")
            return []

    def get_media_comments(self, media_id: str) -> List[Dict]:
        """Get comments for Instagram media"""
        
        try:
            url = f"{self.base_url}/{media_id}/comments"
            params = {
                "access_token": self.access_token,
                "fields": "id,text,username,timestamp,like_count,replies{id,text,username,timestamp}"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            comments = []
            
            for comment in data.get("data", []):
                parsed_comment = self._parse_instagram_comment(comment, media_id)
                comments.append(parsed_comment)
                
                # Add replies
                if "replies" in comment:
                    for reply in comment["replies"]["data"]:
                        parsed_reply = self._parse_instagram_comment(reply, media_id, comment["id"])
                        comments.append(parsed_reply)
            
            logger.info(f"Retrieved {len(comments)} comments for media {media_id}")
            return comments
            
        except Exception as e:
            logger.error(f"Failed to get Instagram comments: {e}")
            return []

    def _parse_instagram_comment(self, comment: Dict, media_id: str, parent_id: str = None) -> Dict:
        """Parse Instagram comment data"""
        
        return {
            "id": comment["id"],
            "media_id": media_id,
            "text": comment.get("text", ""),
            "author": comment.get("username", ""),
            "like_count": comment.get("like_count", 0),
            "published_at": comment.get("timestamp", ""),
            "platform": "instagram",
            "comment_type": "reply" if parent_id else "parent",
            "parent_id": parent_id
        }

    def reply_to_comment(self, comment_id: str, reply_text: str) -> Dict:
        """Reply to an Instagram comment"""
        
        try:
            url = f"{self.base_url}/{comment_id}/replies"
            data = {
                "access_token": self.access_token,
                "message": reply_text
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Successfully replied to Instagram comment {comment_id}")
            return {
                "success": True,
                "reply_id": result["id"],
                "message": "Reply posted successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to reply to Instagram comment {comment_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
