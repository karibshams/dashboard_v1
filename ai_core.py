# ai_core.py - Main AI processing module
import openai
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
import openai
import logging
import os

class AIProcessor:
    def __init__(self, openai_api_key: str):
        """Initialize AI processor with OpenAI API key"""
        openai.api_key = openai_api_key  # Set the API key directly
        self.brand_voice = {
            "tone": "inspirational, authentic, faith-based",
            "style": "conversational, encouraging, professional",
            "values": ["faith", "motivation", "community", "growth"],
            "avoid": ["overly promotional", "generic responses", "religious preaching"]
        }

    def generate_reply(self, prompt: str, model="gpt-3.5-turbo"):
        """Generate a reply based on the prompt."""
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful social media assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7,
        )
        return response.choices[0].message["content"]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommentType(Enum):
    LEAD = "lead"
    PRAISE = "praise" 
    SPAM = "spam"
    QUESTION = "question"
    COMPLAINT = "complaint"
    GENERAL = "general"

class Platform(Enum):
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"

class AIProcessor:
    def __init__(self, openai_api_key: str):
        """Initialize AI processor with OpenAI API key"""
        openai.api_key = openai_api_key
        self.client = openai.OpenAI(api_key=openai_api_key)
        
        # Brand voice configuration for Ervin
        self.brand_voice = {
            "tone": "inspirational, authentic, faith-based",
            "style": "conversational, encouraging, professional",
            "values": ["faith", "motivation", "community", "growth"],
            "avoid": ["overly promotional", "generic responses", "religious preaching"]
        }
        
        # Engagement keywords for GHL triggers
        self.engagement_keywords = {
            "interested": ["interested", "want to know more", "tell me more", "how can i", "sign me up"],
            "purchase_intent": ["price", "cost", "buy", "purchase", "order", "how much"],
            "booking": ["appointment", "call", "consultation", "meeting", "schedule"],
            "support": ["help", "problem", "issue", "not working", "error"],
            "praise": ["amazing", "great", "awesome", "love", "fantastic", "incredible"]
        }

    def classify_comment(self, comment_text: str, platform: str) -> Tuple[CommentType, Dict]:
        """Classify comment type using AI and keyword analysis"""
        
        # First, use keyword-based classification for quick wins
        comment_lower = comment_text.lower()
        
        # Check for spam indicators
        spam_indicators = ["click here", "follow me", "check my profile", "dm me", "www.", "http"]
        if any(indicator in comment_lower for indicator in spam_indicators):
            return CommentType.SPAM, {"confidence": 0.9, "reason": "spam_keywords"}
        
        # Check for lead indicators
        lead_keywords = ["interested", "how much", "price", "buy", "want", "need"]
        if any(keyword in comment_lower for keyword in lead_keywords):
            return CommentType.LEAD, {"confidence": 0.8, "reason": "lead_keywords"}
        
        # Use AI for more nuanced classification
        try:
            classification_prompt = f"""
            Analyze this social media comment and classify it into one of these categories:
            - LEAD: Shows buying interest, asks about services/products, wants more info
            - PRAISE: Compliments, positive feedback, appreciation
            - QUESTION: Asks genuine questions about content/topic
            - COMPLAINT: Negative feedback, problems, dissatisfaction
            - SPAM: Promotional, irrelevant, suspicious content
            - GENERAL: Normal engagement, casual comments
            
            Comment: "{comment_text}"
            Platform: {platform}
            
            Respond with JSON: {{"type": "CATEGORY", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # ✅ supported by all accounts

                messages=[{"role": "user", "content": classification_prompt}],
                temperature=0.6,
                max_tokens=150
            )
            
            result = json.loads(response.choices[0].message.content)
            comment_type = CommentType(result["type"].lower())
            metadata = {
                "confidence": result["confidence"],
                "reasoning": result["reasoning"],
                "ai_classified": True
            }
            
            return comment_type, metadata
            
        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            return CommentType.GENERAL, {"confidence": 0.5, "reason": "fallback", "error": str(e)}

    def generate_reply(self, comment_text: str, comment_type: CommentType, platform: str, 
                      post_context: Optional[str] = None) -> Dict:
        """Generate contextual reply based on comment type and platform"""
        
        try:
            # Build context-aware prompt
            context_info = f"Post context: {post_context}\n" if post_context else ""
            
            system_prompt = f"""
            You are Ervin's AI assistant for social media management. Generate replies that match his brand voice:
            
            BRAND VOICE:
            - Tone: {self.brand_voice['tone']}
            - Style: {self.brand_voice['style']}
            - Core Values: {', '.join(self.brand_voice['values'])}
            - Avoid: {', '.join(self.brand_voice['avoid'])}
            
            REPLY GUIDELINES BY COMMENT TYPE:
            
            LEAD: 
            - Acknowledge interest warmly
            - Provide helpful info without being pushy
            - Include soft CTA (DM, link, tag for updates)
            - Example: "So glad this resonates! I'd love to share more details - check your DMs! 🙏"
            
            PRAISE:
            - Express genuine gratitude
            - Encourage continued engagement
            - Ask engaging follow-up question
            - Example: "Thank you so much! This kind of encouragement keeps me going. What's been your biggest takeaway?"
            
            QUESTION:
            - Provide helpful, specific answer
            - Show expertise without preaching
            - Invite further discussion
            - Example: "Great question! In my experience... What's your current approach to this?"
            
            COMPLAINT:
            - Show empathy and understanding
            - Take responsibility where appropriate
            - Offer solution or follow-up
            - Example: "I hear you and appreciate the feedback. Let me make this right - DMing you now."
            
            GENERAL:
            - Be warm and authentic
            - Add value to the conversation
            - Encourage community engagement
            - Example: "Love seeing this kind of discussion! You all inspire me daily 💪"
            
            PLATFORM CONSIDERATIONS:
            - YouTube: More detailed, educational responses
            - Instagram: Visual, emoji-friendly, shorter
            - Facebook: Community-focused, conversational
            - LinkedIn: Professional but personal
            - Twitter: Concise, impactful
            
            Keep replies 1-3 sentences, natural and conversational. Include relevant emojis for Instagram/Facebook.
            """
            
            user_prompt = f"""
            {context_info}
            Platform: {platform}
            Comment Type: {comment_type.value}
            Comment: "{comment_text}"
            
            Generate an appropriate reply that matches Ervin's brand voice and the comment type guidelines.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # ✅ supported by all accounts

                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6,
                max_tokens=200
            )
            
            reply_text = response.choices[0].message.content.strip()
            
            # Detect GHL trigger keywords in the generated reply and original comment
            ghl_triggers = self._detect_ghl_triggers(comment_text, reply_text)
            
            return {
                "reply": reply_text,
                "platform": platform,
                "comment_type": comment_type.value,
                "ghl_triggers": ghl_triggers,
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.8,
                "needs_approval": self._needs_manual_approval(comment_type, ghl_triggers)
            }
            
        except Exception as e:
            logger.error(f"Reply generation failed: {e}")
            return {
                "reply": "Thanks for your comment! I appreciate you being part of this community. 🙏",
                "platform": platform,
                "comment_type": comment_type.value,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "needs_approval": True
            }

    def _detect_ghl_triggers(self, comment_text: str, reply_text: str) -> Dict:
        """Detect keywords that should trigger GHL workflows"""
        
        triggers = {
            "tags_to_add": [],
            "workflows_to_trigger": [],
            "contact_fields": {}
        }
        
        combined_text = (comment_text + " " + reply_text).lower()
        
        for trigger_type, keywords in self.engagement_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                triggers["tags_to_add"].append(trigger_type)
                
                # Map to specific GHL workflows
                if trigger_type == "interested":
                    triggers["workflows_to_trigger"].append("lead_nurture_sequence")
                elif trigger_type == "purchase_intent":
                    triggers["workflows_to_trigger"].append("sales_follow_up")
                elif trigger_type == "booking":
                    triggers["workflows_to_trigger"].append("appointment_booking")
                elif trigger_type == "support":
                    triggers["workflows_to_trigger"].append("customer_support")
                elif trigger_type == "praise":
                    triggers["workflows_to_trigger"].append("testimonial_request")
        
        return triggers

    def _needs_manual_approval(self, comment_type: CommentType, ghl_triggers: Dict) -> bool:
        """Determine if reply needs manual approval before posting"""
        
        # Always approve praise and general comments
        if comment_type in [CommentType.PRAISE, CommentType.GENERAL]:
            return False
        
        # Require approval for complaints and high-value leads
        if comment_type in [CommentType.COMPLAINT, CommentType.LEAD]:
            return True
        
        # Require approval if it triggers important workflows    
        high_value_workflows = ["sales_follow_up", "appointment_booking"]
        if any(workflow in ghl_triggers.get("workflows_to_trigger", []) for workflow in high_value_workflows):
            return True
        
        return False

    def generate_content(self, content_type: str, topic: str = None, series: str = None, 
                        count: int = 1) -> List[Dict]:
        """Generate content based on type (captions, devotionals, etc.)"""
        
        content_templates = {
            "social_caption": {
                "prompt": "Create an engaging social media caption about {topic}. Include relevant hashtags and a call-to-action.",
                "max_tokens": 300
            },
            "devotional": {
                "prompt": "Write a short daily devotional about {topic}. Include a Bible verse, reflection, and practical application.",
                "max_tokens": 500
            },
            "video_description": {
                "prompt": "Write a YouTube video description for content about {topic}. Include timestamps if relevant and engagement hooks.",
                "max_tokens": 400
            },
            "hashtag_set": {
                "prompt": "Generate 20 relevant hashtags for {topic} content, mixing popular and niche tags.",
                "max_tokens": 200
            }
        }
        
        if content_type not in content_templates:
            raise ValueError(f"Unsupported content type: {content_type}")
        
        template = content_templates[content_type]
        generated_content = []
        
        try:
            for i in range(count):
                series_context = f" as part of the '{series}' series" if series else ""
                
                system_prompt = f"""
                You are Ervin's content creator AI. Generate {content_type} that matches his brand:
                
                Brand Voice: {self.brand_voice['tone']}
                Style: {self.brand_voice['style']}
                Values: {', '.join(self.brand_voice['values'])}
                
                Make it authentic, inspiring, and actionable. Avoid generic motivational clichés.
                """
                
                user_prompt = template["prompt"].format(
                    topic=topic or "personal growth and faith",
                    series=series_context
                )
                
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",  # ✅ supported by all accounts

                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.8,
                    max_tokens=template["max_tokens"]
                )
                
                content = {
                    "type": content_type,
                    "content": response.choices[0].message.content.strip(),
                    "topic": topic,
                    "series": series,
                    "created_at": datetime.now().isoformat(),
                    "status": "draft",
                    "id": f"{content_type}_{datetime.now().timestamp()}_{i}"
                }
                
                generated_content.append(content)
                
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise
        
        return generated_content

    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of comment/message"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "user", 
                    "content": f"""Analyze the sentiment of this text and respond with JSON:
                    
                    Text: "{text}"
                    
                    Response format: 
                    {{
                        "sentiment": "positive/negative/neutral",
                        "confidence": 0.0-1.0,
                        "emotions": ["joy", "anger", "curiosity", etc.],
                        "urgency": "low/medium/high"
                    }}
                    """
                }],
                temperature=0.6,
                max_tokens=150
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "emotions": ["unknown"],
                "urgency": "low",
                "error": str(e)
            }
