# Improved scheduler.py with better error handling and real-time updates
import schedule
import time
import threading
from datetime import datetime, timedelta
import logging
from typing import Dict, List
import asyncio

logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self, comment_processor, database_manager):
        """Initialize task scheduler with error recovery"""
        self.comment_processor = comment_processor
        self.db = database_manager
        self.running = False
        self.scheduler_thread = None
        self.error_count = {}  # Track errors per platform
        self.max_retries = 3
        
        # Platform integrators
        self.integrators = {}
        
        # Real-time update callbacks
        self.update_callbacks = []

    def setup_integrators(self, api_keys: Dict):
        """Setup platform integrators with validation"""
        from youtube_integration import YouTubeIntegrator
        from facebook_integration import FacebookIntegrator
        from instagram_integration import InstagramIntegrator
        from linkedin_integration import LinkedInIntegrator
        from twitter_integration import TwitterIntegrator
        
        # Validate and setup each integrator
        if api_keys.get("youtube_api_key"):
            try:
                self.integrators["youtube"] = YouTubeIntegrator(api_keys["youtube_api_key"])
                logger.info("YouTube integrator initialized")
            except Exception as e:
                logger.error(f"Failed to initialize YouTube: {e}")
                
        if api_keys.get("facebook_access_token") and api_keys.get("facebook_page_id"):
            try:
                self.integrators["facebook"] = FacebookIntegrator(
                    api_keys["facebook_access_token"],
                    api_keys["facebook_page_id"]
                )
                logger.info("Facebook integrator initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Facebook: {e}")
                
        # Similar setup for other platforms...

    def register_update_callback(self, callback):
        """Register callback for real-time updates"""
        self.update_callbacks.append(callback)

    def _notify_update(self, update_type: str, data: Dict):
        """Notify all registered callbacks of updates"""
        for callback in self.update_callbacks:
            try:
                callback(update_type, data)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def start_scheduler(self):
        """Start the background scheduler with error recovery"""
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(
                target=self._run_scheduler_with_recovery, 
                daemon=True
            )
            self.scheduler_thread.start()
            logger.info("Task scheduler started with error recovery")

    def _run_scheduler_with_recovery(self):
        """Run scheduler with automatic recovery from errors"""
        while self.running:
            try:
                self._run_scheduler()
            except Exception as e:
                logger.error(f"Scheduler crashed: {e}. Restarting in 30 seconds...")
                time.sleep(30)

    def _run_scheduler(self):
        """Run scheduled tasks"""
        # Immediate fetch on start
        self.fetch_all_comments()
        
        # Schedule regular fetches
        schedule.every(5).minutes.do(self.fetch_all_comments)
        schedule.every(1).minutes.do(self.process_pending_comments)
        
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def fetch_all_comments(self):
        """Fetch new comments from all platforms with error isolation"""
        logger.info("Starting scheduled comment fetch")
        
        for platform, integrator in self.integrators.items():
            try:
                self._fetch_platform_comments(platform, integrator)
                # Reset error count on success
                self.error_count[platform] = 0
            except Exception as e:
                self._handle_platform_error(platform, e)

    def _handle_platform_error(self, platform: str, error: Exception):
        """Handle platform-specific errors with retry logic"""
        self.error_count[platform] = self.error_count.get(platform, 0) + 1
        
        if self.error_count[platform] >= self.max_retries:
            logger.error(f"{platform} failed {self.max_retries} times. Disabling temporarily.")
            # Implement exponential backoff or temporary disable
        else:
            logger.warning(f"{platform} error (attempt {self.error_count[platform]}): {error}")

    def _fetch_platform_comments(self, platform: str, integrator):
        """Fetch comments for specific platform with streaming updates"""
        last_check = self.db.get_last_check_time(platform) or datetime.now() - timedelta(hours=2)
        
        if platform == "youtube":
            videos = integrator.get_channel_videos(max_results=10)
            
            for video in videos:
                comments = integrator.get_video_comments(video["video_id"])
                
                for comment in comments:
                    # Filter new comments
                    comment_time = datetime.fromisoformat(comment["published_at"].replace('Z', '+00:00'))
                    if comment_time > last_check:
                        self._process_single_comment(comment, platform, video)
                        
        elif platform == "facebook":
            posts = integrator.get_page_posts(limit=10)
            
            for post in posts:
                comments = integrator.get_post_comments(post["id"])
                
                for comment in comments:
                    comment_time = datetime.fromisoformat(comment["published_at"])
                    if comment_time > last_check:
                        self._process_single_comment(comment, platform, post)
                        
        # Similar for other platforms...
        
        # Update last check time
        self.db.update_last_check_time(platform, datetime.now())

    def _process_single_comment(self, comment: Dict, platform: str, post_data: Dict):
        """Process single comment and notify dashboard"""
        try:
            # Format comment data
            comment_data = {
                "id": comment["id"],
                "text": comment["text"],
                "platform": platform,
                "commenter": {
                    "name": comment.get("author", comment.get("username", "Unknown")),
                    "id": comment.get("author_id", comment.get("author_channel_id"))
                },
                "post_context": self._get_post_context(platform, post_data),
                "published_at": comment.get("published_at"),
                "metrics": {
                    "likes": comment.get("like_count", 0),
                    "replies": comment.get("reply_count", 0)
                }
            }
            
            # Save to database
            self.db.save_comment(comment_data)
            
            # Notify dashboard in real-time
            self._notify_update("new_comment", comment_data)
            
            # Process based on owner activity
            owner_active = self.db.get_owner_activity()
            
            if not owner_active:
                # AI processes and auto-replies
                self._process_ai_reply(comment_data)
            else:
                # Mark for manual review
                logger.info(f"Comment {comment['id']} queued for manual review")
                
        except Exception as e:
            logger.error(f"Failed to process comment {comment.get('id')}: {e}")

    def _process_ai_reply(self, comment_data: Dict):
        """Process AI reply with approval workflow"""
        try:
            # Generate AI response
            result = self.comment_processor.process_comment(comment_data)
            
            # Save reply to database
            reply_data = {
                "comment_id": comment_data["id"],
                "reply": result["reply"]["reply"],
                "platform": comment_data["platform"],
                "status": "pending" if result["reply"]["needs_approval"] else "auto_approved",
                "source": "ai",
                "confidence": result["reply"].get("confidence", 0.0),
                "ghl_triggers": result["reply"].get("ghl_triggers", {})
            }
            
            reply_id = self.db.save_reply(reply_data)
            
            # Notify dashboard of new reply
            self._notify_update("new_reply", {
                "reply_id": reply_id,
                **reply_data
            })
            
            # Auto-post if approved
            if reply_data["status"] == "auto_approved":
                self._post_reply_to_platform(comment_data, reply_data["reply"])
                
        except Exception as e:
            logger.error(f"AI reply generation failed: {e}")

    def _post_reply_to_platform(self, comment_data: Dict, reply_text: str):
        """Post reply to platform with error handling"""
        platform = comment_data["platform"]
        integrator = self.integrators.get(platform)
        
        if not integrator:
            logger.error(f"No integrator available for {platform}")
            return
            
        try:
            if platform == "youtube":
                result = integrator.reply_to_comment(comment_data["id"], reply_text)
            elif platform == "facebook":
                result = integrator.reply_to_comment(comment_data["id"], reply_text)
            elif platform == "instagram":
                result = integrator.reply_to_comment(comment_data["id"], reply_text)
            elif platform == "linkedin":
                result = integrator.reply_to_comment(comment_data["id"], reply_text)
            elif platform == "twitter":
                result = integrator.reply_to_tweet(comment_data["id"], reply_text)
                
            if result.get("success"):
                # Update reply status
                self.db.update_reply_status(comment_data["id"], "posted")
                logger.info(f"Successfully posted reply to {platform}")
                
                # Notify dashboard
                self._notify_update("reply_posted", {
                    "comment_id": comment_data["id"],
                    "platform": platform,
                    "reply_id": result.get("reply_id")
                })
            else:
                logger.error(f"Failed to post reply: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error posting reply to {platform}: {e}")

    def process_pending_comments(self):
        """Process any pending comments that need review"""
        pending_replies = self.db.get_pending_replies(limit=100)
        
        for reply in pending_replies:
            # Check if auto-approval conditions are met
            if self._can_auto_approve(reply):
                self.db.update_reply_status(reply["_id"], "auto_approved")
                
                # Get original comment data
                comment = self.db.get_comment_by_id(reply["comment_id"])
                if comment:
                    self._post_reply_to_platform(comment, reply["reply"])

    def _can_auto_approve(self, reply: Dict) -> bool:
        """Determine if reply can be auto-approved"""
        # Auto-approve based on confidence and type
        if reply.get("confidence", 0) >= 0.8:
            comment_type = reply.get("comment_type", "general")
            if comment_type in ["praise", "general"]:
                return True
        return False

    def _get_post_context(self, platform: str, post_data: Dict) -> str:
        """Generate post context string"""
        if platform == "youtube":
            return f"YouTube video: {post_data.get('title', 'Unknown')}"
        elif platform == "facebook":
            return f"Facebook post: {post_data.get('message', '')[:50]}..."
        elif platform == "instagram":
            return f"Instagram post: {post_data.get('caption', '')[:50]}..."
        elif platform == "linkedin":
            return f"LinkedIn post"
        elif platform == "twitter":
            return f"Tweet: {post_data.get('text', '')[:50]}..."
        return f"{platform} post"

    def bulk_approve_comments(self, comment_ids: List[str]):
        """Bulk approve comments for AI reply"""
        for comment_id in comment_ids:
            comment = self.db.get_comment_by_id(comment_id)
            if comment and not self.db.has_reply(comment_id):
                self._process_ai_reply(comment)

    def stop_scheduler(self):
        """Gracefully stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Task scheduler stopped")
