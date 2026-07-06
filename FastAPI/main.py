from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional
from pymongo import MongoClient
from bson import ObjectId
import hashlib
import secrets

app = FastAPI(title="Notes App")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# MongoDB
client = MongoClient("mongodb+srv://bhaikshreyansh_db_user:Shreyansh%4004@cluster0.rmspwfd.mongodb.net/?appName=Cluster0")
db = client["notesdb"]
notes_collection = db["notes"]
users_collection = db["users"]

# Session store
sessions = {}

# Helpers
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def note_serializer(note) -> dict:
    return {
        "id": str(note["_id"]),
        "title": note["title"],
        "content": note["content"],
        "important": note.get("important", False),
        "owner": note.get("owner", "")
    }

def get_current_user(request: Request):
    token = request.cookies.get("session_token")
    if token and token in sessions:
        return sessions[token]
    return None

# ── Auth Routes ──────────────────────────────

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="register.html", context={"error": None}
    )

@app.post("/register", response_class=HTMLResponse)
def register(request: Request, username: str = Form(...), password: str = Form(...)):
    if users_collection.find_one({"username": username}):
        return templates.TemplateResponse(
            request=request, name="register.html", context={"error": "Username already exists!"}
        )
    users_collection.insert_one({"username": username, "password": hash_password(password)})
    return RedirectResponse("/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="login.html", context={"error": None}
    )

@app.post("/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = users_collection.find_one({"username": username, "password": hash_password(password)})
    if not user:
        return templates.TemplateResponse(
            request=request, name="login.html", context={"error": "Invalid username or password!"}
        )
    token = secrets.token_hex(16)
    sessions[token] = username
    response = RedirectResponse("/notes", status_code=302)
    response.set_cookie("session_token", token)
    return response

@app.get("/logout")
def logout(request: Request):
    token = request.cookies.get("session_token")
    if token in sessions:
        del sessions[token]
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("session_token")
    return response

# ── Notes Routes ─────────────────────────────

@app.get("/")
def home():
    return RedirectResponse("/notes", status_code=302)

@app.get("/notes", response_class=HTMLResponse)
def get_notes(request: Request, search: Optional[str] = None):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    query = {"owner": user}
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}}
        ]
    notes = [note_serializer(n) for n in notes_collection.find(query)]
    return templates.TemplateResponse(
        request=request, name="notes.html", context={"notes": notes, "user": user, "search": search or ""}
    )

@app.post("/notes/create")
def create_note(request: Request, title: str = Form(...), content: str = Form(...), important: Optional[str] = Form(None)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    notes_collection.insert_one({"title": title, "content": content, "important": important == "on", "owner": user})
    return RedirectResponse("/notes", status_code=302)

@app.get("/notes/edit/{note_id}", response_class=HTMLResponse)
def edit_note_page(note_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    note = notes_collection.find_one({"_id": ObjectId(note_id), "owner": user})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return templates.TemplateResponse(
        request=request, name="edit.html", context={"note": note_serializer(note), "user": user}
    )

@app.post("/notes/edit/{note_id}")
def edit_note(note_id: str, request: Request, title: str = Form(...), content: str = Form(...), important: Optional[str] = Form(None)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    notes_collection.update_one(
        {"_id": ObjectId(note_id), "owner": user},
        {"$set": {"title": title, "content": content, "important": important == "on"}}
    )
    return RedirectResponse("/notes", status_code=302)

@app.get("/notes/delete/{note_id}")
def delete_note(note_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    notes_collection.delete_one({"_id": ObjectId(note_id), "owner": user})
    return RedirectResponse("/notes", status_code=302)
