# linkedin_integration.py - LinkedIn API integration
import requests
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class LinkedInIntegrator:
    def __init__(self, access_token: str, organization_id: str = None):
        """Initialize LinkedIn API client"""
        self.access_token = access_token
        self.organization_id = organization_id
        self.base_url = "https://api.linkedin.com/v2"
        
    def get_posts(self, limit: int = 25) -> List[Dict]:
        """Get recent LinkedIn posts"""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # Get posts for organization or person
            if self.organization_id:
                url = f"{self.base_url}/shares"
                params = {
                    "q": "owners",
                    "owners": f"urn:li:organization:{self.organization_id}",
                    "count": limit
                }
            else:
                url = f"{self.base_url}/shares"
                params = {"q": "owners", "owners": "urn:li:person:current", "count": limit}
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            posts = data.get("elements", [])
            
            logger.info(f"Retrieved {len(posts)} LinkedIn posts")
            return posts
            
        except Exception as e:
            logger.error(f"Failed to get LinkedIn posts: {e}")
            return []

    def get_post_comments(self, post_urn: str) -> List[Dict]:
        """Get comments for a LinkedIn post"""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            url = f"{self.base_url}/socialActions/{post_urn}/comments"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            comments = []
            
            for comment in data.get("elements", []):
                parsed_comment = self._parse_linkedin_comment(comment, post_urn)
                comments.append(parsed_comment)
            
            logger.info(f"Retrieved {len(comments)} comments for LinkedIn post")
            return comments
            
        except Exception as e:
            logger.error(f"Failed to get LinkedIn comments: {e}")
            return []

    def _parse_linkedin_comment(self, comment: Dict, post_urn: str) -> Dict:
        """Parse LinkedIn comment data"""
        
        return {
            "id": comment.get("id", ""),
            "post_urn": post_urn,
            "text": comment.get("message", {}).get("text", ""),
            "author": comment.get("actor", ""),
            "published_at": comment.get("created", {}).get("time", ""),
            "platform": "linkedin"
        }
