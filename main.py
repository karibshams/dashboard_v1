import logging
import os
from scheduler import TaskScheduler
from database_manager import DatabaseManager
from comment_processor import CommentProcessor
import threading

def run_scheduler():
    db = DatabaseManager()
    comment_processor = CommentProcessor(os.getenv("OPENAI_API_KEY"))
    scheduler = TaskScheduler(comment_processor, db)
    api_keys = {
        "youtube_api_key": os.getenv("YOUTUBE_API_KEY"),
        "facebook_access_token": os.getenv("FACEBOOK_ACCESS_TOKEN"),
        "facebook_page_id": os.getenv("FACEBOOK_PAGE_ID"),
        "instagram_access_token": os.getenv("INSTAGRAM_ACCESS_TOKEN"),
        "instagram_business_account_id": os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID"),
        "linkedin_access_token": os.getenv("LINKEDIN_ACCESS_TOKEN"),
        "linkedin_organization_id": os.getenv("LINKEDIN_ORGANIZATION_ID"),
        "twitter_bearer_token": os.getenv("TWITTER_BEARER_TOKEN"),
        "twitter_api_key": os.getenv("TWITTER_API_KEY"),
        "twitter_api_secret": os.getenv("TWITTER_API_SECRET"),
        "twitter_access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
        "twitter_access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    }
    scheduler.setup_integrators(api_keys)
    scheduler.start_scheduler()

def run_api():
    import uvicorn
    from api_server import app
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    run_api()