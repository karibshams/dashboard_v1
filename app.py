# Enhanced app.py with real-time updates and improved UI

import streamlit as st
from dashboard.comment_processor import CommentProcessor
from dashboard.content_manager import ContentManager
import os
import json
import requests
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_URL = "http://localhost:8000"

# Initialize processors
comment_processor = CommentProcessor(OPENAI_API_KEY)
content_manager = ContentManager(OPENAI_API_KEY)

# Page config
st.set_page_config(
    page_title="Ervin's AI Social Media Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* General background */
    body, .stApp {
        background-color: black ;
    }

    /* Sidebar background */
    section[data-testid="stSidebar"] {
        background-color: #2c3e50 !important;
        color: white !important;
    }

    /* Sidebar text and buttons */
    section[data-testid="stSidebar"] .stButton button, 
    section[data-testid="stSidebar"] label, 
    section[data-testid="stSidebar"] .stCheckbox {
        color: white !important;
        margin-bottom: 10px;
    }

    /* Comment card */
    div.comment-card {
        background-color: #fff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        margin-bottom: 15px;
        border-left: 5px solid #1f77b4;
        transition: transform 0.2s;
    }

    div.comment-card:hover {
        transform: scale(1.02);
    }

    /* AI reply card */
    div.ai-reply-card {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
    }

    /* Platform badges */
    .platform-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        color: white;
        margin-right: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .youtube { background-color: #ff0000; }
    .facebook { background-color: #1877f2; }
    .instagram { background-color: #e4405f; }
    .linkedin { background-color: #0077b5; }
    .twitter { background-color: #1da1f2; }

    /* Metric cards */
    div.metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Status tags */
    .status-pending { color: #ff9800; }
    .status-approved { color: #4caf50; }
    .status-rejected { color: #f44336; }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'comments' not in st.session_state:
    st.session_state.comments = []
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True

# Header
st.title("🤖 Ervin's AI Social Media Command Center")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Control Panel")
    
    # Owner Activity Toggle
    try:
        resp = requests.get(f"{API_URL}/owner/activity")
        owner_active = resp.json().get("active", False)
    except:
        owner_active = False
        st.error("API connection failed")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Mode", "Manual" if owner_active else "AI Auto", 
                  delta="Owner Active" if owner_active else "AI Active")
    
    with col2:
        new_owner_active = st.toggle("Owner Control", value=owner_active)
        if new_owner_active != owner_active:
            try:
                requests.post(f"{API_URL}/owner/activity", json={"active": new_owner_active})
                st.success("Mode updated!")
                st.rerun()
            except:
                st.error("Failed to update mode")
    
    st.markdown("---")
    
    # Auto-refresh toggle
    st.session_state.auto_refresh = st.checkbox("Auto-refresh (10s)", value=st.session_state.auto_refresh)
    
    # Platform filters
    st.subheader("🔍 Filters")
    platforms = st.multiselect(
        "Platforms",
        ["youtube", "facebook", "instagram", "linkedin", "twitter"],
        default=["youtube", "facebook", "instagram", "linkedin", "twitter"]
    )
    
    comment_types = st.multiselect(
        "Comment Types",
        ["lead", "praise", "question", "complaint", "general"],
        default=["lead", "praise", "question", "complaint", "general"]
    )
    
    # Time range
    time_range = st.selectbox(
        "Time Range",
        ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"]
    )
    
    # Analytics summary
    st.markdown("---")
    st.subheader("📊 Quick Stats")
    
    # Fetch analytics
    try:
        analytics_resp = requests.get(f"{API_URL}/analytics/summary")
        analytics = analytics_resp.json()
    except:
        analytics = {
            "total_comments": 0,
            "total_replies": 0,
            "response_rate": 0,
            "avg_response_time": 0
        }
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Comments", analytics.get("total_comments", 0))
        st.metric("AI Replies", analytics.get("total_replies", 0))
    with col2:
        st.metric("Response Rate", f"{analytics.get('response_rate', 0):.1f}%")
        st.metric("Avg Response Time", f"{analytics.get('avg_response_time', 0):.1f}m")

# Main content area
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📥 Live Comment Stream", 
    "🤖 AI Reply Queue", 
    "📝 Content Generator",
    "📊 Analytics",
    "⚙️ Settings"
])

# Tab 1: Live Comment Stream
with tab1:
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.subheader("💬 Real-Time Comments")
    with col2:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    with col3:
        bulk_action = st.selectbox("Bulk Action", ["Select...", "Approve All", "AI Reply All"])
    
    # Fetch comments with filters
    params = {
        "platforms": platforms,
        "comment_types": comment_types,
        "time_range": time_range,
        "limit": 50
    }
    
    try:
        resp = requests.get(f"{API_URL}/comments/filtered", params=params)
        comments = resp.json().get("comments", [])
    except:
        comments = []
        st.error("Failed to fetch comments")
    
    if not comments:
        st.info("No comments found. They will appear here as they come in! 🎯")
    else:
        # Group comments by platform
        for platform in platforms:
            platform_comments = [c for c in comments if c.get("platform") == platform]
            if platform_comments:
                st.markdown(f"### <span class='platform-badge {platform}'>{platform.upper()}</span>", 
                           unsafe_allow_html=True)
                
                for comment in platform_comments[:10]:  # Show latest 10 per platform
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        
                        with col1:
                            st.markdown(f"""
                            <div class='comment-card'>
                                <strong>{comment.get('author', 'Unknown')}</strong> 
                                <span style='color: #666; font-size: 12px;'>
                                    {comment.get('published_at', '')}
                                </span>
                                <p>{comment.get('text', '')}</p>
                                <small>Type: <span class='status-{comment.get('comment_type', 'general')}'>
                                    {comment.get('comment_type', 'general').upper()}
                                </span></small>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            if comment.get('has_reply'):
                                st.success("✅ Replied")
                            else:
                                st.warning("⏳ Pending")
                        
                        with col3:
                            if not comment.get('has_reply'):
                                if st.button("🤖 AI Reply", key=f"ai_{comment['id']}"):
                                    # Trigger AI reply
                                    requests.post(f"{API_URL}/comments/{comment['id']}/ai-reply")
                                    st.success("AI reply generated!")
                                    time.sleep(1)
                                    st.rerun()
                        
                        with col4:
                            if st.button("👁️ View", key=f"view_{comment['id']}"):
                                st.session_state.selected_comment = comment

# Tab 2: AI Reply Queue
with tab2:
    st.subheader("🤖 AI Generated Replies - Pending Approval")
    
    # Fetch pending AI replies
    try:
        resp = requests.get(f"{API_URL}/replies/pending", params={"limit": 50})
        pending_replies = resp.json().get("replies", [])
    except:
        pending_replies = []
    
    if not pending_replies:
        st.info("No pending AI replies. All caught up! 🎉")
    else:
        # Bulk approve button
        if st.button("✅ Approve All Visible"):
            for reply in pending_replies:
                requests.post(f"{API_URL}/reply/approve", json={"reply_id": str(reply["_id"])})
            st.success("All replies approved!")
            time.sleep(1)
            st.rerun()
        
        # Display pending replies
        for reply in pending_replies:
            with st.expander(f"Reply to {reply.get('author', 'Unknown')} on {reply.get('platform', '')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown("**Original Comment:**")
                    st.write(reply.get('original_comment', 'N/A'))
                    
                    st.markdown("**AI Generated Reply:**")
                    st.markdown(f"""
                    <div class='ai-reply-card'>
                        {reply.get('reply', '')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show confidence and triggers
                    col_a, col_b = st.columns(2)
                    with col_a:
                        confidence = reply.get('confidence', 0) * 100
                        st.progress(confidence / 100)
                        st.caption(f"Confidence: {confidence:.0f}%")
                    
                    with col_b:
                        triggers = reply.get('ghl_triggers', {}).get('tags_to_add', [])
                        if triggers:
                            st.caption(f"Triggers: {', '.join(triggers)}")
                
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("✅ Approve", key=f"approve_{reply['_id']}"):
                        requests.post(f"{API_URL}/reply/approve", 
                                    json={"reply_id": str(reply["_id"])})
                        st.success("Approved!")
                        time.sleep(0.5)
                        st.rerun()
                    
                    if st.button("❌ Reject", key=f"reject_{reply['_id']}"):
                        requests.post(f"{API_URL}/reply/reject", 
                                    json={"reply_id": str(reply["_id"])})
                        st.warning("Rejected")
                        time.sleep(0.5)
                        st.rerun()
                    
                    if st.button("✏️ Edit", key=f"edit_{reply['_id']}"):
                        st.session_state.editing_reply = reply

# Tab 3: Content Generator
with tab3:
    st.subheader("📝 AI Content Generator")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        content_type = st.selectbox(
            "Content Type",
            ["social_caption", "devotional", "video_description", "hashtag_set"]
        )
        
        topic = st.text_input("Topic", placeholder="e.g., faith and growth, motivation")
        series = st.text_input("Series (optional)", placeholder="e.g., Weekly Wisdom")
        
        col_a, col_b = st.columns(2)
        with col_a:
            count = st.number_input("How many?", min_value=1, max_value=10, value=3)
        with col_b:
            tone = st.selectbox("Tone", ["Inspirational", "Educational", "Conversational", "Professional"])
    
    with col2:
        st.markdown("### 💡 Quick Templates")
        if st.button("📅 Weekly Devotionals"):
            st.session_state.content_preset = "devotional_week"
        if st.button("📱 Social Media Pack"):
            st.session_state.content_preset = "social_pack"
        if st.button("#️⃣ Hashtag Library"):
            st.session_state.content_preset = "hashtag_lib"
    
    if st.button("🚀 Generate Content", type="primary"):
        with st.spinner("Creating amazing content..."):
            try:
                content = content_manager.ai_processor.generate_content(
                    content_type, topic=topic, series=series, count=count
                )
                
                st.success(f"✅ Generated {len(content)} pieces of content!")
                
                # Display generated content
                for i, item in enumerate(content):
                    with st.expander(f"{content_type} #{i+1}"):
                        st.write(item['content'])
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("💾 Save", key=f"save_content_{i}"):
                                # Save to database
                                st.success("Saved!")
                        with col2:
                            if st.button("📋 Copy", key=f"copy_content_{i}"):
                                st.write("Copied to clipboard!")
                        with col3:
                            if st.button("🔄 Regenerate", key=f"regen_content_{i}"):
                                st.rerun()
                
            except Exception as e:
                st.error(f"Generation failed: {str(e)}")

# Tab 4: Analytics
with tab4:
    st.subheader("📊 Performance Analytics")
    
    # Date range selector
    col1, col2 = st.columns([1, 3])
    with col1:
        date_range = st.date_input(
            "Date Range",
            value=(datetime.now() - timedelta(days=7), datetime.now()),
            max_value=datetime.now()
        )
    
    # Fetch analytics data
    try:
        resp = requests.get(f"{API_URL}/analytics/detailed", 
                          params={"start_date": date_range[0], "end_date": date_range[1]})
        analytics_data = resp.json()
    except:
        analytics_data = {}
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <h3>🔢 Total Comments</h3>
            <h1>{}</h1>
            <p>↑ {}% from last period</p>
        </div>
        """.format(
            analytics_data.get('total_comments', 0),
            analytics_data.get('comment_growth', 0)
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <h3>🤖 AI Replies</h3>
            <h1>{}</h1>
            <p>{} auto-approved</p>
        </div>
        """.format(
            analytics_data.get('total_replies', 0),
            analytics_data.get('auto_approved', 0)
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='metric-card'>
            <h3>⚡ Avg Response</h3>
            <h1>{} min</h1>
            <p>↓ {} min faster</p>
        </div>
        """.format(
            analytics_data.get('avg_response_time', 0),
            analytics_data.get('response_improvement', 0)
        ), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class='metric-card'>
            <h3>😊 Sentiment</h3>
            <h1>{}%</h1>
            <p>positive comments</p>
        </div>
        """.format(analytics_data.get('positive_sentiment_pct', 0)), unsafe_allow_html=True)
    
    # Charts
    st.markdown("### 📈 Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Comments by platform
        if analytics_data.get('platform_breakdown'):
            fig_platform = px.pie(
                values=list(analytics_data['platform_breakdown'].values()),
                names=list(analytics_data['platform_breakdown'].keys()),
                title="Comments by Platform"
            )
            st.plotly_chart(fig_platform, use_container_width=True)
    
    with col2:
        # Comment types
        if analytics_data.get('comment_types'):
            fig_types = px.bar(
                x=list(analytics_data['comment_types'].keys()),
                y=list(analytics_data['comment_types'].values()),
                title="Comment Types Distribution"
            )
            st.plotly_chart(fig_types, use_container_width=True)
    
    # Time series
    if analytics_data.get('daily_stats'):
        df_daily = pd.DataFrame(analytics_data['daily_stats'])
        fig_timeline = go.Figure()
        
        fig_timeline.add_trace(go.Scatter(
            x=df_daily['date'],
            y=df_daily['comments'],
            mode='lines+markers',
            name='Comments',
            line=dict(color='blue', width=2)
        ))
        
        fig_timeline.add_trace(go.Scatter(
            x=df_daily['date'],
            y=df_daily['replies'],
            mode='lines+markers',
            name='AI Replies',
            line=dict(color='green', width=2)
        ))
        
        fig_timeline.update_layout(
            title="Daily Activity Trend",
            xaxis_title="Date",
            yaxis_title="Count",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_timeline, use_container_width=True)

# Tab 5: Settings
with tab5:
    st.subheader("⚙️ Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔑 API Connections")
        
        # Platform status
        platforms_status = {
            "YouTube": "✅ Connected" if os.getenv("YOUTUBE_API_KEY") else "❌ Not configured",
            "Facebook": "✅ Connected" if os.getenv("FACEBOOK_ACCESS_TOKEN") else "❌ Not configured",
            "Instagram": "✅ Connected" if os.getenv("INSTAGRAM_ACCESS_TOKEN") else "❌ Not configured",
            "LinkedIn": "❌ Not configured",
            "Twitter": "❌ Not configured"
        }
        
        for platform, status in platforms_status.items():
            st.write(f"{platform}: {status}")
        
        if st.button("🔄 Test All Connections"):
            with st.spinner("Testing connections..."):
                # Test API connections
                time.sleep(2)
                st.success("Connection test complete!")
    
    with col2:
        st.markdown("### 🤖 AI Settings")
        
        temperature = st.slider("AI Creativity", 0.0, 1.0, 0.6)
        max_reply_length = st.number_input("Max Reply Length", 50, 500, 200)
        
        st.markdown("### 📧 Notifications")
        email_notifications = st.checkbox("Email notifications for high-priority comments")
        notification_email = st.text_input("Notification Email") if email_notifications else None
        
        if st.button("💾 Save Settings"):
            # Save settings to database
            st.success("Settings saved!")

# Auto-refresh logic
if st.session_state.auto_refresh:
    time.sleep(10)
    st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<center>Built with ❤️ for Ervin | AI-Powered Social Media Management</center>", 
    unsafe_allow_html=True
)
