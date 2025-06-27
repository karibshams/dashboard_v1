from .ai_core import AIProcessor
from .ghl_integration import GHLIntegrator
from typing import Dict, List
from datetime import datetime
import logging

from . import facebook_integration, instagram_integration, youtube_integration, linkedin_integration, twitter_integration
from .database_manager import DatabaseManager  # Add the DatabaseManager import

logger = logging.getLogger(__name__)

class CommentProcessor:
    def __init__(self, openai_api_key: str, ghl_api_key: str = None, db: DatabaseManager = None):
        """Initialize comment processor with AI, GHL integration, and database manager"""
        self.ai_processor = AIProcessor(openai_api_key)
        self.ghl_integrator = GHLIntegrator(ghl_api_key)
        self.db = db  # Pass the database manager instance to store data

    def process_comment(self, comment_data: Dict) -> Dict:
        """Main workflow to process incoming comments"""
        try:
            # Extract comment information
            comment_text = comment_data["text"]
            platform = comment_data["platform"]
            commenter_info = comment_data.get("commenter", {})
            post_context = comment_data.get("post_context")

            # Step 1: Classify comment
            comment_type, classification_meta = self.ai_processor.classify_comment(comment_text, platform)

            # Step 2: Generate reply
            reply_data = self.ai_processor.generate_reply(comment_text, comment_type, platform, post_context)

            # Step 3: Analyze sentiment
            sentiment_data = self.ai_processor.analyze_sentiment(comment_text)

            # Step 4: Handle GHL integration if needed
            ghl_response = None
            if reply_data.get("ghl_triggers", {}).get("workflows_to_trigger"):
                # Create and update contact
                contact_data = {
                    "name": commenter_info.get("name", "Unknown"),
                    "email": commenter_info.get("email"),
                    "phone": commenter_info.get("phone"),
                    "platform": platform,
                    "tags": reply_data["ghl_triggers"]["tags_to_add"],
                    "comment_text": comment_text,
                    "custom_fields": {
                        "comment_sentiment": sentiment_data["sentiment"],
                        "comment_type": comment_type.value,
                        "engagement_platform": platform
                    }
                }

                contact_result = self.ghl_integrator.create_or_update_contact(contact_data)

                if contact_result["success"]:
                    # Trigger workflows
                    for workflow in reply_data["ghl_triggers"]["workflows_to_trigger"]:
                        self.ghl_integrator.trigger_workflow(workflow, contact_result["contact_id"], {
                            "comment_text": comment_text,
                            "platform": platform,
                            "sentiment": sentiment_data["sentiment"]
                        })

                ghl_response = contact_result

            # Save processed comment to database
            comment_data["classification"] = {"type": comment_type.value, "metadata": classification_meta}
            comment_data["reply"] = reply_data["reply"]
            comment_data["sentiment"] = sentiment_data
            comment_data["ghl_integration"] = ghl_response
            comment_data["processing_timestamp"] = datetime.now().isoformat()
            comment_data["status"] = "processed"
            comment_data["needs_approval"] = reply_data.get("needs_approval", False)

            # Save to the database
            self.db.save_comment(comment_data)

            logger.info(f"Successfully processed and saved comment: {comment_data.get('id')}")
            return comment_data

        except Exception as e:
            logger.error(f"Comment processing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "original_comment": comment_data.get("text", ""),
                "platform": comment_data.get("platform", "")
            }
