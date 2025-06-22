# twitter_integration.py - Twitter/X API integration (v2)
import tweepy
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class TwitterIntegrator:
    def __init__(self, bearer_token: str, api_key: str = None, api_secret: str = None, 
                 access_token: str = None, access_token_secret: str = None):
        """Initialize Twitter API v2 client"""
        
        self.bearer_token = bearer_token
        
        # Initialize API v2 client for reading
        self.client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True
        )
        
        logger.info("Twitter API client initialized")

    def get_user_tweets(self, username: str, max_results: int = 100) -> List[Dict]:
        """Get recent tweets from user"""
        
        try:
            # Get user ID first
            user = self.client.get_user(username=username)
            if not user.data:
                logger.error(f"User {username} not found")
                return []
            
            user_id = user.data.id
            
            # Get tweets
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics', 'conversation_id']
            )
            
            if not tweets.data:
                return []
            
            parsed_tweets = []
            for tweet in tweets.data:
                parsed_tweet = {
                    "id": tweet.id,
                    "text": tweet.text,
                    "created_at": tweet.created_at.isoformat() if tweet.created_at else "",
                    "conversation_id": tweet.conversation_id,
                    "public_metrics": tweet.public_metrics,
                    "platform": "twitter"
                }
                parsed_tweets.append(parsed_tweet)
            
            logger.info(f"Retrieved {len(parsed_tweets)} tweets")
            return parsed_tweets
            
        except Exception as e:
            logger.error(f"Failed to get tweets: {e}")
            return []

    def get_tweet_replies(self, tweet_id: str) -> List[Dict]:
        """Get replies to a specific tweet"""
        
        try:
            # Search for replies using conversation_id
            tweets = self.client.search_recent_tweets(
                query=f"conversation_id:{tweet_id}",
                tweet_fields=['created_at', 'author_id', 'in_reply_to_user_id'],
                max_results=100
            )
            
            if not tweets.data:
                return []
            
            replies = []
            for tweet in tweets.data:
                if tweet.id != tweet_id:  # Exclude original tweet
                    reply = {
                        "id": tweet.id,
                        "text": tweet.text,
                        "author_id": tweet.author_id,
                        "created_at": tweet.created_at.isoformat() if tweet.created_at else "",
                        "in_reply_to_user_id": tweet.in_reply_to_user_id,
                        "platform": "twitter",
                        "original_tweet_id": tweet_id
                    }
                    replies.append(reply)
            
            logger.info(f"Retrieved {len(replies)} replies to tweet {tweet_id}")
            return replies
            
        except Exception as e:
            logger.error(f"Failed to get tweet replies: {e}")
            return []

    def reply_to_tweet(self, tweet_id: str, reply_text: str) -> Dict:
        """Reply to a tweet"""
        
        try:
            response = self.client.create_tweet(
                text=reply_text,
                in_reply_to_tweet_id=tweet_id
            )
            
            logger.info(f"Successfully replied to tweet {tweet_id}")
            return {
                "success": True,
                "reply_id": response.data['id'],
                "message": "Reply posted successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to reply to tweet {tweet_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
