from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from .database_manager import DatabaseManager
from .comment_processor import CommentProcessor
import os

app = FastAPI()
db = DatabaseManager()
comment_processor = CommentProcessor(os.getenv("OPENAI_API_KEY"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/comments")
def get_comments(limit: int = 50):
    comments = list(db.comments.find().sort("created_at", -1).limit(limit))
    for c in comments:
        c["_id"] = str(c["_id"])
    return {"comments": comments}

@app.get("/replies/pending")
def get_pending_replies(limit: int = 50):
    replies = list(db.replies.find({"status": "pending"}).sort("created_at", -1).limit(limit))
    for r in replies:
        r["_id"] = str(r["_id"])
    return {"replies": replies}

@app.post("/reply/owner")
def owner_reply(data: dict = Body(...)):
    reply_data = {
        "comment_id": data["comment_id"],
        "reply": data["reply_text"],
        "platform": data["platform"],
        "status": "approved",
        "source": "owner"
    }
    db.save_reply(reply_data)
    return {"status": "ok"}

@app.post("/owner/activity")
def set_owner_activity(data: dict = Body(...)):
    db.set_owner_activity(data.get("active", False))
    return {"status": "ok"}

@app.get("/owner/activity")
def get_owner_activity():
    return {"active": db.get_owner_activity()}

@app.post("/reply/approve")
def approve_ai_reply(data: dict = Body(...)):
    db.update_reply_status(data["reply_id"], "approved")
    return {"status": "ok"}

@app.post("/reply/reject")
def reject_ai_reply(data: dict = Body(...)):
    db.update_reply_status(data["reply_id"], "rejected")
    return {"status": "ok"}