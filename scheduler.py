# scheduler.py - Background task scheduler
import schedule
import time
import threading
from datetime import datetime, timedelta
import logging

from youtube_integration import YouTubeIntegrator
from facebook_integration import FacebookIntegrator
from instagram_integration import InstagramIntegrator
from linkedin_integration import LinkedInIntegrator
from twitter_integration import TwitterIntegrator
from typing import Dict

logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self, comment_processor, database_manager):
        """Initialize task scheduler"""
        self.comment_processor = comment_processor
        self.db = database_manager
        self.running = False
        self.scheduler_thread = None

        # Platform integrators (to be initialized with API keys)
        self.youtube_integrator = None
        self.facebook_integrator = None
        self.instagram_integrator = None
        self.linkedin_integrator = None
        self.twitter_integrator = None

    def setup_integrators(self, api_keys: Dict):
        """Setup platform integrators with API keys"""
        if api_keys.get("youtube_api_key"):
            self.youtube_integrator = YouTubeIntegrator(api_keys["youtube_api_key"])
        if api_keys.get("facebook_access_token"):
            self.facebook_integrator = FacebookIntegrator(
                api_keys["facebook_access_token"],
                api_keys.get("facebook_page_id")
            )
        if api_keys.get("instagram_access_token"):
            self.instagram_integrator = InstagramIntegrator(
                api_keys["instagram_access_token"],
                api_keys["instagram_business_account_id"]
            )
        if api_keys.get("linkedin_access_token"):
            self.linkedin_integrator = LinkedInIntegrator(
                api_keys["linkedin_access_token"],
                api_keys.get("linkedin_organization_id")
            )
        if api_keys.get("twitter_bearer_token"):
            self.twitter_integrator = TwitterIntegrator(api_keys["twitter_bearer_token"])

    def start_scheduler(self):
        """Start the background scheduler thread"""
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            logger.info("Task scheduler started.")

    def _run_scheduler(self):
        """Run scheduled tasks"""
        schedule.every(10).minutes.do(self.fetch_all_comments)
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def fetch_all_comments(self):
        """Fetch new comments from all platforms"""
        logger.info("Starting scheduled comment fetch")
        last_check = datetime.now() - timedelta(hours=2)
        if self.youtube_integrator:
            self._fetch_youtube_comments(last_check)
        if self.facebook_integrator:
            self._fetch_facebook_comments()
        if self.instagram_integrator:
            self._fetch_instagram_comments()
        if self.linkedin_integrator:
            self._fetch_linkedin_comments()
        if self.twitter_integrator:
            self._fetch_twitter_mentions()

    def _fetch_youtube_comments(self, last_check: datetime):
        try:
            new_comments = self.youtube_integrator.get_new_comments_since(last_check)
            for comment in new_comments:
                comment_data = {
                    "id": comment["id"],
                    "text": comment["text"],
                    "platform": "youtube",
                    "commenter": {
                        "name": comment["author"],
                        "id": comment["author_channel_id"]
                    },
                    "post_context": f"YouTube video: {comment['video_id']}"
                }
                self._process_and_reply(comment_data)
                logger.info(f"Processed YouTube comment: {comment['id']}")
        except Exception as e:
            logger.error(f"Failed to fetch YouTube comments: {e}")

    def _fetch_facebook_comments(self):
        # Implement similar to _fetch_youtube_comments
        pass

    def _fetch_instagram_comments(self):
        # Implement similar to _fetch_youtube_comments
        pass

    def _fetch_linkedin_comments(self):
        # Implement similar to _fetch_youtube_comments
        pass

    def _fetch_twitter_mentions(self):
        # Implement similar to _fetch_youtube_comments
        pass

    def _process_and_reply(self, comment_data):
        """Process comment and reply based on owner activity"""
        self.db.save_comment(comment_data)
        if self.db.get_owner_activity():
            # Wait for owner to reply via dashboard
            logger.info("Owner is active. Waiting for manual reply.")
            return
        # AI processes and replies
        result = self.comment_processor.process_comment(comment_data)
        self.db.save_reply(result)
        self._post_reply_to_platform(comment_data, result["reply"]["reply"])

    def _post_reply_to_platform(self, comment_data, reply_text):
        platform = comment_data["platform"]
        if platform == "youtube" and self.youtube_integrator:
            self.youtube_integrator.reply_to_comment(comment_data["id"], reply_text)
        elif platform == "facebook" and self.facebook_integrator:
            self.facebook_integrator.reply_to_comment(comment_data["id"], reply_text)
        elif platform == "instagram" and self.instagram_integrator:
            self.instagram_integrator.reply_to_comment(comment_data["id"], reply_text)
        elif platform == "linkedin" and self.linkedin_integrator:
            self.linkedin_integrator.reply_to_comment(comment_data["id"], reply_text)
        elif platform == "twitter" and self.twitter_integrator:
            self.twitter_integrator.reply_to_comment(comment_data["id"], reply_text)