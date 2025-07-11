# 🧠 AI Social Media Dashboard

An AI-powered social media engagement dashboard designed for Ervin's brand to:

✅ Auto-classify comments and generate AI replies
✅ Maintain brand tone with manual/auto reply control
✅ Generate social captions, devotionals, hashtags
✅ View recent replies with status tracking

---

## 🚀 Features

* **Comment Analyzer & AI Auto-Reply**

  * Tags comment type (question, praise, lead, complaint, etc.)
  * Generates platform-specific replies using AI (supports GPT-4 or Groq's LLaMA3)
  * Owner can toggle between manual and AI reply mode

* **Content Generator**

  * Creates social captions, devotional outlines, hashtags, and video descriptions
  * Supports generating multiple drafts at once

* **Reply Monitoring**

  * View pending or recent replies pulled from the API server
  * Shows platform, source (AI or Manual), status, and timestamps

---

## 🗂 Folder Structure

```
ervin_social_dashboard/
├── .env                   # API keys and environment config
├── app.py                 # Streamlit AI Dashboard
├── api_server.py          # FastAPI backend (run separately)
├── main.py                # AI module test runner
├── requirements.txt       # Dependencies
├── README.md               # You're reading this
├── dashboard/
│   ├── ai/                # AI components (reply engine, classifier, content generator)
│   ├── ai_core.py
│   ├── comment_processor.py
│   ├── content_manager.py
│   ├── other integrations (youtube, facebook, etc.)
```

---

## ⚙️ Setup Instructions

### 1️⃣ Install Requirements

```bash
pip install -r requirements.txt
```

### 2️⃣ Environment Setup

Create a `.env` file in the root with:

```
OPENAI_API_KEY=sk-...
GROQ_API_KEY=your-groq-api-key
```

If using the API backend:

```
API_URL=http://localhost:8000
```

---

## 🖥 Run the Streamlit Dashboard

```bash
streamlit run app.py
```

Dashboard will open at [http://localhost:8501](http://localhost:8501)

---

## 🌐 Backend API Server (Optional)

For full functionality (owner activity toggle, reply history), run:

```bash
python api_server.py
```

---

## 💡 Notes

* AI replies support OpenAI GPT-4 or Groq's LLaMA models (switchable)
* Owner "active" toggle lets you control manual vs AI replies
* Works with YouTube, Facebook, Instagram, LinkedIn, Twitter

---

## 🛠 Future Enhancements

* Auto-fetching new comments every few minutes
* Voice-based replies (planned)
* Full GoHighLevel CRM triggers

