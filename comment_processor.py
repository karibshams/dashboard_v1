# comment_processor.py - Main comment processing workflow
from .ai_core import AIProcessor
from .ghl_integration import GHLIntegrator
from typing import Dict, List
from datetime import datetime
import logging

from . import facebook_integration, instagram_integration, youtube_integration, linkedin_integration, twitter_integration

logger = logging.getLogger(__name__)

class CommentProcessor:
    def __init__(self, openai_api_key: str, ghl_api_key: str = None):
        """Initialize comment processor with AI and GHL integration"""
        self.ai_processor = AIProcessor(openai_api_key)
        self.ghl_integrator = GHLIntegrator(ghl_api_key)

    def process_comment(self, comment_data: Dict) -> Dict:
        """Main workflow to process incoming comments"""

        try:
            # Extract comment information
            comment_text = comment_data["text"]
            platform = comment_data["platform"]
            commenter_info = comment_data.get("commenter", {})
            post_context = comment_data.get("post_context")

            # Step 1: Classify comment
            comment_type, classification_meta = self.ai_processor.classify_comment(
                comment_text, platform
            )

            # Step 2: Generate reply
            reply_data = self.ai_processor.generate_reply(
                comment_text, comment_type, platform, post_context
            )

            # Step 3: Analyze sentiment
            sentiment_data = self.ai_processor.analyze_sentiment(comment_text)

            # Step 4: Handle GHL integration if needed
            ghl_response = None
            if reply_data.get("ghl_triggers", {}).get("workflows_to_trigger"):

                # Create contact data
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

                # Create/update contact
                contact_result = self.ghl_integrator.create_or_update_contact(contact_data)

                if contact_result["success"]:
                    # Trigger workflows
                    for workflow in reply_data["ghl_triggers"]["workflows_to_trigger"]:
                        self.ghl_integrator.trigger_workflow(
                            workflow,
                            contact_result["contact_id"],
                            {
                                "comment_text": comment_text,
                                "platform": platform,
                                "sentiment": sentiment_data["sentiment"]
                            }
                        )

                ghl_response = contact_result

            # Combine all results
            processing_result = {
                "comment_id": comment_data.get("id", f"comment_{datetime.now().timestamp()}"),
                "original_comment": comment_text,
                "platform": platform,
                "classification": {
                    "type": comment_type.value,
                    "metadata": classification_meta
                },
                "reply": reply_data,
                "sentiment": sentiment_data,
                "ghl_integration": ghl_response,
                "processing_timestamp": datetime.now().isoformat(),
                "status": "processed",
                "needs_approval": reply_data.get("needs_approval", False)
            }

            logger.info(f"Successfully processed comment: {comment_data.get('id')}")
            return processing_result

        except Exception as e:
            logger.error(f"Comment processing failed: {e}")

            # Structured error response
            error_info = {
                "message": str(e),
                "type": type(e).__name__,
                "code": getattr(e, "code", "unknown")
            }

            return {
                "comment_id": comment_data.get("id", f"comment_{datetime.now().timestamp()}"),
                "original_comment": comment_data.get("text", ""),
                "platform": comment_data.get("platform", ""),
                "classification": {
                    "type": "error",
                    "metadata": {
                        "confidence": 0.0,
                        "reason": "fallback",
                        "error": error_info
                    }
                },
                "sentiment": {
                    "sentiment": "unknown",
                    "confidence": 0.0,
                    "emotions": ["unknown"],
                    "urgency": "low",
                    "error": error_info
                },
                "reply": {
                    "reply": "⚠️ AI could not generate a reply due to an error.",
                    "ghl_triggers": {}
                },
                "ghl_integration": None,
                "processing_timestamp": datetime.now().isoformat(),
                "status": "error",
                "needs_approval": False
            }

    def process_comments_batch(self, comments: List[Dict], owner_active: bool):
        """
        Process a batch of comments.
        If owner_active is True, comments are shown for manual reply.
        If owner_active is False, AI auto-replies and posts to the platform.
        """
        for comment in comments:
            if owner_active:
                # Show in dashboard for manual reply (implement this in your dashboard UI)
                logger.info(f"Owner active: showing comment {comment.get('id')} for manual reply.")
                continue
            else:
                result = self.process_comment(comment)
                reply_text = result["reply"].get("reply")
                platform = comment.get("platform")
                comment_id = comment.get("id")
                # Post reply to the correct platform
                if platform == "facebook":
                    facebook_integration.post_comment_reply(comment_id, reply_text)
                elif platform == "instagram":
                    instagram_integration.post_comment_reply(comment_id, reply_text)
                elif platform == "youtube":
                    youtube_integration.post_comment_reply(comment_id, reply_text)
                elif platform == "linkedin":
                    linkedin_integration.post_comment_reply(comment_id, reply_text)
                elif platform == "twitter":
                    twitter_integration.post_comment_reply(comment_id, reply_text)
                logger.info(f"AI replied to comment {comment_id} on {platform}.")