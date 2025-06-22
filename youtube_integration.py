# youtube_integration.py - YouTube API integration for comment fetching
import googleapiclient.discovery
import googleapiclient.errors
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
import time

logger = logging.getLogger(__name__)

class YouTubeIntegrator:
    def __init__(self, api_key: str):
        """Initialize YouTube API client"""
        self.api_key = api_key
        self.api_service_name = "youtube"
        self.api_version = "v3"
        
        try:
            self.youtube = googleapiclient.discovery.build(
                self.api_service_name, 
                self.api_version, 
                developerKey=api_key
            )
            logger.info("YouTube API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube API: {e}")
            raise

    def get_channel_videos(self, channel_id: str = None, max_results: int = 50) -> List[Dict]:
        """Get recent videos from channel"""
        
        try:
            # If no channel_id provided, get the authenticated user's channel
            if not channel_id:
                channels_response = self.youtube.channels().list(
                    part="id,snippet",
                    mine=True
                ).execute()
                
                if not channels_response.get("items"):
                    raise ValueError("No channel found for authenticated user")
                
                channel_id = channels_response["items"][0]["id"]
            
            # Get channel's upload playlist
            channel_response = self.youtube.channels().list(
                part="contentDetails",
                id=channel_id
            ).execute()
            
            uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            
            # Get videos from uploads playlist
            playlist_response = self.youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=max_results
            ).execute()
            
            videos = []
            for item in playlist_response["items"]:
                video_data = {
                    "video_id": item["snippet"]["resourceId"]["videoId"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "published_at": item["snippet"]["publishedAt"],
                    "thumbnail": item["snippet"]["thumbnails"]["default"]["url"],
                    "channel_id": channel_id
                }
                videos.append(video_data)
            
            logger.info(f"Retrieved {len(videos)} videos from channel")
            return videos
            
        except Exception as e:
            logger.error(f"Failed to get channel videos: {e}")
            return []

    def get_video_comments(self, video_id: str, max_results: int = 100) -> List[Dict]:
        """Get comments for a specific video"""
        
        try:
            comments = []
            next_page_token = None
            
            while len(comments) < max_results:
                request = self.youtube.commentThreads().list(
                    part="snippet,replies",
                    videoId=video_id,
                    maxResults=min(100, max_results - len(comments)),
                    order="time",  # Get newest comments first
                    pageToken=next_page_token
                )
                
                response = request.execute()
                
                for item in response["items"]:
                    comment_data = self._parse_comment_thread(item, video_id)
                    comments.append(comment_data)
                    
                    # Also get replies if any
                    if "replies" in item:
                        for reply in item["replies"]["comments"]:
                            reply_data = self._parse_reply(reply, video_id, comment_data["id"])
                            comments.append(reply_data)
                
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
            
            logger.info(f"Retrieved {len(comments)} comments for video {video_id}")
            return comments[:max_results]
            
        except googleapiclient.errors.HttpError as e:
            if e.resp.status == 403:
                logger.warning(f"Comments disabled for video {video_id}")
                return []
            else:
                logger.error(f"YouTube API error getting comments: {e}")
                return []
        except Exception as e:
            logger.error(f"Failed to get video comments: {e}")
            return []

    def _parse_comment_thread(self, comment_thread: Dict, video_id: str) -> Dict:
        """Parse comment thread data"""
        
        snippet = comment_thread["snippet"]["topLevelComment"]["snippet"]
        
        return {
            "id": comment_thread["id"],
            "video_id": video_id,
            "text": snippet["textDisplay"],
            "author": snippet["authorDisplayName"],
            "author_channel_id": snippet.get("authorChannelId", {}).get("value"),
            "like_count": snippet.get("likeCount", 0),
            "published_at": snippet["publishedAt"],
            "updated_at": snippet.get("updatedAt", snippet["publishedAt"]),
            "platform": "youtube",
            "comment_type": "parent",
            "parent_id": None,
            "reply_count": comment_thread["snippet"].get("totalReplyCount", 0),
            "can_reply": snippet.get("canReply", True)
        }

    def _parse_reply(self, reply: Dict, video_id: str, parent_id: str) -> Dict:
        """Parse reply comment data"""
        
        snippet = reply["snippet"]
        
        return {
            "id": reply["id"],
            "video_id": video_id,
            "text": snippet["textDisplay"],
            "author": snippet["authorDisplayName"],
            "author_channel_id": snippet.get("authorChannelId", {}).get("value"),
            "like_count": snippet.get("likeCount", 0),
            "published_at": snippet["publishedAt"],
            "updated_at": snippet.get("updatedAt", snippet["publishedAt"]),
            "platform": "youtube",
            "comment_type": "reply",
            "parent_id": parent_id,
            "reply_count": 0,
            "can_reply": True
        }

    def get_new_comments_since(self, last_check: datetime, channel_id: str = None) -> List[Dict]:
        """Get all new comments since last check"""
        
        try:
            # Get recent videos
            videos = self.get_channel_videos(channel_id, max_results=10)
            
            all_new_comments = []
            
            # Complete the youtube_integration.py file (continuation from where it was cut off)

            for video in videos:
                # Only check videos published after last_check
                video_published = datetime.fromisoformat(video["published_at"].replace('Z', '+00:00'))
                if video_published > last_check:
                    video_comments = self.get_video_comments(video["video_id"])
                    
                    # Filter comments newer than last_check
                    new_comments = [
                        comment for comment in video_comments 
                        if datetime.fromisoformat(comment["published_at"].replace('Z', '+00:00')) > last_check
                    ]
                    
                    all_new_comments.extend(new_comments)
                    
                    # Rate limiting
                    time.sleep(0.1)
            
            logger.info(f"Found {len(all_new_comments)} new comments since {last_check}")
            return all_new_comments
            
        except Exception as e:
            logger.error(f"Failed to get new comments: {e}")
            return []

    def reply_to_comment(self, comment_id: str, reply_text: str) -> Dict:
        """Reply to a YouTube comment"""
        
        try:
            response = self.youtube.comments().insert(
                part="snippet",
                body={
                    "snippet": {
                        "parentId": comment_id,
                        "textOriginal": reply_text
                    }
                }
            ).execute()
            
            logger.info(f"Successfully replied to comment {comment_id}")
            return {
                "success": True,
                "reply_id": response["id"],
                "message": "Reply posted successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to reply to comment {comment_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
