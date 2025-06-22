# app.py
import streamlit as st
from dashboard.comment_processor import CommentProcessor
from dashboard.content_manager import ContentManager
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_URL = "http://localhost:8000"  # Change if your FastAPI server runs elsewhere

# Initialize processors
comment_processor = CommentProcessor(OPENAI_API_KEY)
content_manager = ContentManager(OPENAI_API_KEY)

# Streamlit App
st.set_page_config(page_title="Ervin's AI Dashboard", layout="centered")
st.title("🧠 Ervin's Social AI Assistant")

# -------- Owner Activity Toggle --------
st.sidebar.header("⚙️ Owner Activity")
try:
    resp = requests.get(f"{API_URL}/owner/activity")
    owner_active = resp.json().get("active", False)
except Exception:
    owner_active = False
    st.sidebar.warning("Could not connect to API server for owner status.")

new_owner_active = st.sidebar.toggle("Owner Active (Manual Reply)", value=owner_active)
if new_owner_active != owner_active:
    try:
        requests.post(f"{API_URL}/owner/activity", json={"active": new_owner_active})
        st.sidebar.success("Owner activity updated!")
    except Exception:
        st.sidebar.error("Failed to update owner activity.")

st.sidebar.write(f"**Current Mode:** {'Manual (Owner)' if new_owner_active else 'Auto (AI)'}")

# Tabs for functionality
tab1, tab2, tab3 = st.tabs(["💬 Comment AI", "📝 Content Generator", "🗨️ Recent Replies"])

# -------- Tab 1: Comment Classification & Reply --------
with tab1:
    st.subheader("Classify a Comment + Auto-Generate Reply")

    comment_text = st.text_area("Enter a social media comment", height=100)
    platform = st.selectbox("Platform", ["youtube", "facebook", "instagram", "linkedin", "twitter"])

    if st.button("🔍 Analyze & Generate Reply"):
        with st.spinner("Processing..."):
            comment_data = {
                "id": "test_123",
                "text": comment_text,
                "platform": platform,
                "commenter": {"name": "Test User"},
                "post_context": "motivational post"
            }
            result = comment_processor.process_comment(comment_data)

        if "error" in result["classification"]["metadata"]:
            st.error("❌ AI Reply Not Generated - Quota or API Error")
            st.write("### 🚫 Error Details")
            error_detail = result["classification"]["metadata"]["error"]
            try:
                st.json(json.loads(error_detail))
            except Exception:
                st.code(str(error_detail))
        else:
            st.success("✅ AI Reply Generated")
            st.write("### 🧠 Classification")
            st.json(result["classification"])
            st.write("### 🤖 AI Reply")
            st.markdown(result["reply"]["reply"])
            st.write("### 🔖 Sentiment")
            st.json(result["sentiment"])

# -------- Tab 2: Content Generation --------
with tab2:
    st.subheader("Generate Captions or Devotionals")

    content_type = st.selectbox("Content Type", ["social_caption", "devotional", "video_description", "hashtag_set"])
    topic = st.text_input("Topic", value="faith and growth")
    series = st.text_input("Series (optional)", value="")
    count = st.slider("How many?", 1, 5, 1)

    if st.button("✍️ Generate Content"):
        with st.spinner("Generating..."):
            content = content_manager.ai_processor.generate_content(content_type, topic=topic, series=series, count=count)

        st.success("✅ Content Generated")
        for c in content:
            st.markdown(f"**• {c['type']}**: {c['content']}")

# -------- Tab 3: Recent Replies & Posting Status --------
with tab3:
    st.subheader("Recent Replies & Posting Status")
    try:
        resp = requests.get(f"{API_URL}/replies/pending?limit=20")
        replies = resp.json().get("replies", [])
        if not replies:
            st.info("No recent replies found.")
        else:
            for reply in replies:
                st.markdown(f"""
                **Comment ID:** {reply.get('comment_id')}
                **Reply:** {reply.get('reply')}
                **Platform:** {reply.get('platform')}
                **Status:** {reply.get('status', 'pending').capitalize()}
                **Source:** {reply.get('source', 'AI')}
                **Created At:** {reply.get('created_at', '')}
                ---
                """)
    except Exception as e:
        st.error(f"Could not fetch replies: {e}")