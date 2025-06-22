# facebook_integration.py - Facebook/Instagram API integration
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class FacebookIntegrator:
    def __init__(self, access_token: str, page_id: str = None):
        """Initialize Facebook Graph API client"""
        self.access_token = access_token
        self.page_id = page_id
        self.base_url = "https://graph.facebook.com/v18.0"
        
    def get_page_posts(self, limit: int = 25) -> List[Dict]:
        """Get recent posts from Facebook page"""
        
        try:
            url = f"{self.base_url}/{self.page_id}/posts"
            params = {
                "access_token": self.access_token,
                "limit": limit,
                "fields": "id,message,created_time,permalink_url,comments{id,message,from,created_time,like_count}"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            posts = data.get("data", [])
            
            logger.info(f"Retrieved {len(posts)} Facebook posts")
            return posts
            
        except Exception as e:
            logger.error(f"Failed to get Facebook posts: {e}")
            return []

    def get_post_comments(self, post_id: str) -> List[Dict]:
        """Get comments for a specific Facebook post"""
        
        try:
            url = f"{self.base_url}/{post_id}/comments"
            params = {
                "access_token": self.access_token,
                "fields": "id,message,from,created_time,like_count,comments{id,message,from,created_time}"
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            comments = []
            
            for comment in data.get("data", []):
                parsed_comment = self._parse_facebook_comment(comment, post_id)
                comments.append(parsed_comment)
                
                # Add nested replies
                if "comments" in comment:
                    for reply in comment["comments"]["data"]:
                        parsed_reply = self._parse_facebook_comment(reply, post_id, comment["id"])
                        comments.append(parsed_reply)
            
            logger.info(f"Retrieved {len(comments)} comments for post {post_id}")
            return comments
            
        except Exception as e:
            logger.error(f"Failed to get Facebook comments: {e}")
            return []

    def _parse_facebook_comment(self, comment: Dict, post_id: str, parent_id: str = None) -> Dict:
        """Parse Facebook comment data"""
        
        return {
            "id": comment["id"],
            "post_id": post_id,
            "text": comment.get("message", ""),
            "author": comment["from"]["name"],
            "author_id": comment["from"]["id"],
            "like_count": comment.get("like_count", 0),
            "published_at": comment["created_time"],
            "platform": "facebook",
            "comment_type": "reply" if parent_id else "parent",
            "parent_id": parent_id
        }

    def reply_to_comment(self, comment_id: str, reply_text: str) -> Dict:
        """Reply to a Facebook comment"""
        
        try:
            url = f"{self.base_url}/{comment_id}/comments"
            data = {
                "access_token": self.access_token,
                "message": reply_text
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"Successfully replied to Facebook comment {comment_id}")
            return {
                "success": True,
                "reply_id": result["id"],
                "message": "Reply posted successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to reply to Facebook comment {comment_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
