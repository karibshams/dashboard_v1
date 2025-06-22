from .ai_core import AIProcessor
from typing import List, Dict

# content_manager.py - Content generation and management
class ContentManager:
    def __init__(self, openai_api_key: str):
        """Initialize content manager"""
        self.ai_processor = AIProcessor(openai_api_key)
        
    def bulk_generate_captions(self, topics: List[str], series: str = None) -> List[Dict]:
        """Generate multiple social media captions"""
        
        all_captions = []
        for topic in topics:
            captions = self.ai_processor.generate_content(
                "social_caption", topic=topic, series=series, count=3
            )
            all_captions.extend(captions)
        
        return all_captions
    
    def generate_devotional_series(self, theme: str, count: int = 7) -> List[Dict]:
        """Generate a series of devotionals"""
        
        devotionals = self.ai_processor.generate_content(
            "devotional", topic=theme, series=f"{theme} Weekly Series", count=count
        )
        
        # Add day numbers to series
        for i, devotional in enumerate(devotionals, 1):
            devotional["day_number"] = i
            devotional["series_title"] = f"{theme} - Day {i}"
        
        return devotionals
    
    def generate_hashtag_library(self, categories: List[str]) -> Dict:
        """Generate hashtag sets for different content categories"""
        
        hashtag_library = {}
        for category in categories:
            hashtags = self.ai_processor.generate_content(
                "hashtag_set", topic=category, count=1
            )
            hashtag_library[category] = hashtags[0]["content"]
        
        return hashtag_library

# Example usage and configuration
if __name__ == "__main__":
    # Initialize with your API keys
    OPENAI_API_KEY = "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"
    
    # Example content generation
    content_manager = ContentManager(OPENAI_API_KEY)
    
    # Generate captions
    captions = content_manager.bulk_generate_captions(
        ["faith and business", "morning motivation", "personal growth"],
        series="Weekly Inspiration"
    )
    
    # Generate devotional series
    devotionals = content_manager.generate_devotional_series("Overcoming Fear", 5)
    
    print(f"Generated {len(captions)} captions and {len(devotionals)} devotionals")

