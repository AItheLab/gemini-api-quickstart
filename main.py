from fastapi import FastAPI, HTTPException, Request, Response, UploadFile, File, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any # Ensure Any is imported
from PIL import Image
import io
import os
import uuid
import asyncio
import json # Added for JSON operations
from pathlib import Path # Added for path manipulation
import aiofiles # Added for async file operations
from dotenv import load_dotenv

from google import genai
# Removed incorrect import: from google.generativeai.types import Chat as GenAIChat

# Load environment variables from .env file
load_dotenv()

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# Check if API key is set
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY environment variable is not set. Please set it in your .env file.")

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Create FastAPI app
app = FastAPI(
    title="Gemini API Server",
    description="API server for Gemini AI model interactions",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active chat sessions and pending data
chat_sessions: Dict[str, Any] = {}
pending_messages: Dict[str, str] = {}
pending_images: Dict[str, Image.Image] = {}

# Directory for storing chat histories
CHAT_HISTORY_DIR = Path("chat_histories")
CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True) # Create directory if it doesn't exist

# Pydantic models for request/response validation
class MessageRequest(BaseModel):
    message: str

class SessionResponse(BaseModel):
    success: bool
    session_id: str

class MessageResponse(BaseModel):
    success: bool

class HistoryItem(BaseModel):
    role: str
    content: str

class HistoryResponse(BaseModel):
    success: bool
    history: List[HistoryItem]

class ErrorResponse(BaseModel):
    success: bool = False
    message: str

class HealthResponse(BaseModel):
    status: str

def allowed_file(filename: str) -> bool:
    """Returns if a filename has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

async def get_session_id(x_session_id: str = Header(...)):
    """Dependency to validate session ID header"""
    if not x_session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")
    return x_session_id

async def get_session_id_flexible(
    x_session_id: Optional[str] = Header(None),
    session_id: Optional[str] = Query(None)
):
    """Get session ID from either header or query parameter"""
    # Priorizar el header, pero usar el query parameter si el header no está presente
    effective_session_id = x_session_id or session_id
    
    if not effective_session_id:
        raise HTTPException(status_code=400, detail="Missing session ID")
    return effective_session_id

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session():
    """Creates a new chat session"""
    session_id = str(uuid.uuid4())
    # _get_or_create_chat_session will create and cache it
    await _get_or_create_chat_session(session_id) 
    return {
        "success": True,
        "session_id": session_id
    }

# Helper function to consolidate SDK history list for output
def _consolidate_sdk_history_for_output(sdk_history_list: List[Any]) -> List[Dict[str, str]]:
    """
    Consolidates a list of SDK message objects, merging consecutive model messages
    and ensuring a clean list of {'role': ..., 'content': ...} dicts.
    """
    consolidated_messages = []
    i = 0
    while i < len(sdk_history_list):
        sdk_msg = sdk_history_list[i]
        current_role = sdk_msg.role if sdk_msg.role in ["user", "model"] else "model"
        
        current_content_parts = []
        if sdk_msg.parts:
            for part in sdk_msg.parts:
                if hasattr(part, 'text') and part.text:
                    current_content_parts.append(part.text)
        full_content = " ".join(current_content_parts)

        if current_role == "model":
            j = i + 1
            while j < len(sdk_history_list):
                next_sdk_msg = sdk_history_list[j]
                next_role = next_sdk_msg.role if next_sdk_msg.role in ["user", "model"] else "model"
                if next_role == "model":
                    next_content_parts = []
                    if next_sdk_msg.parts:
                        for part_next in next_sdk_msg.parts:
                            if hasattr(part_next, 'text') and part_next.text:
                                next_content_parts.append(part_next.text)
                    if next_content_parts:
                        full_content = (full_content + " " + " ".join(next_content_parts)).strip()
                    j += 1
                else:
                    break 
            i = j - 1 
        
        if full_content.strip() or current_role == "user":
            consolidated_messages.append({
                "role": current_role,
                "content": full_content.strip()
            })
        i += 1
    return consolidated_messages

@app.get("/api/sessions/{session_id}", response_model=HistoryResponse)
async def get_session_history(session_id: str): # Renamed for clarity from get_session
    """Get the history of a chat session"""
    chat_session_obj = await _get_or_create_chat_session(session_id)
    
    history_from_sdk = chat_session_obj.get_history() # This might be fragmented by the SDK
    
    # Consolidate the history before sending to frontend
    final_formatted_history = _consolidate_sdk_history_for_output(history_from_sdk)
        
    return {
        "success": True,
        "history": final_formatted_history
    }

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Depends(get_session_id)
):
    """Upload an image file for multi-modal processing"""
    # Ensure session object is loaded/created and cached
    await _get_or_create_chat_session(session_id) 
        
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check if file type is allowed
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="File type not allowed")
    
    # Read file content
    contents = await file.read()
    file_stream = io.BytesIO(contents)
    file_stream.seek(0)
    
    try:
        pending_images[session_id] = Image.open(file_stream)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

    return {
        "success": True,
        "message": "File uploaded successfully and added to the conversation",
        "filename": file.filename
    }

@app.post("/api/chat", response_model=MessageResponse)
async def chat(
    message_request: MessageRequest,
    session_id: str = Depends(get_session_id)
):
    """Save a message to be processed by the AI"""
    # Ensure session object is loaded/created and cached
    chat_session_obj = await _get_or_create_chat_session(session_id)
    
    pending_messages[session_id] = message_request.message
    
    return {"success": True}

@app.get("/api/stream")
async def stream(
    session_id: str = Depends(get_session_id_flexible)
):
    """Stream the AI response to a message"""
    print(f"Attempting to stream for session_id: {session_id}")
    
    chat_session_obj = await _get_or_create_chat_session(session_id)
    
    if session_id not in pending_messages and session_id not in pending_images:
        print(f"No pending message or image for session_id: {session_id}. Pending messages: {list(pending_messages.keys())}, Pending images: {list(pending_images.keys())}")
        raise HTTPException(status_code=400, detail="No pending message or image to process")

    message_text = pending_messages.get(session_id, "") 
    image_obj = pending_images.get(session_id)
    
    print(f"Pending content for session_id {session_id}: Text='{message_text}', Image present: {image_obj is not None}")
    
    async def generate():
        try:
            send_payload = []
            if message_text:
                send_payload.append(message_text)
            if image_obj:
                send_payload.append(image_obj)

            if not send_payload: 
                 yield "data: [Error: No content to send]\n\n"
                 yield "data: [DONE]\n\n"
                 return

            response = chat_session_obj.send_message_stream(send_payload)

            for chunk in response:
                if hasattr(chunk, 'text') and chunk.text:
                    yield f"data: {chunk.text}\n\n"
            
            sdk_history_list = chat_session_obj.get_history()
            consolidated_history_to_save = _consolidate_sdk_history_for_output(sdk_history_list)
            await save_history_to_file(session_id, consolidated_history_to_save)

        except Exception as e:
            print(f"Error during stream generation or history saving for {session_id}: {e}")
            yield f"data: [Error: {str(e)}]\n\n"
        finally:
            if session_id in pending_messages:
                del pending_messages[session_id]
            if session_id in pending_images:
                del pending_images[session_id]
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

# Helper functions for persistent chat history
async def save_history_to_file(session_id: str, history: List[Dict[str, Any]]):
    """Saves chat history to a JSON file."""
    filepath = CHAT_HISTORY_DIR / f"{session_id}.json"
    try:
        async with aiofiles.open(filepath, "w") as f:
            await f.write(json.dumps(history, indent=2))
        print(f"History saved for session {session_id} to {filepath}")
    except Exception as e:
        print(f"Error saving history for session {session_id}: {e}")

async def load_history_from_file(session_id: str) -> Optional[List[Dict[str, Any]]]:
    """Loads chat history from a JSON file."""
    filepath = CHAT_HISTORY_DIR / f"{session_id}.json"
    if not filepath.exists():
        return None
    try:
        async with aiofiles.open(filepath, "r") as f:
            content = await f.read()
            history = json.loads(content)
        print(f"History loaded for session {session_id} from {filepath}")
        return history
    except Exception as e:
        print(f"Error loading history for session {session_id}: {e}")
        return None

async def _get_or_create_chat_session(session_id: str) -> Any: # Changed type hint to Any
    """
    Retrieves an existing chat session or creates a new one,
    loading history from file if available.
    """
    if session_id in chat_sessions:
        return chat_sessions[session_id]

    loaded_history_data = await load_history_from_file(session_id)
    
    sdk_history_to_init = []
    if loaded_history_data:
        for msg_data in loaded_history_data:
            if "content" in msg_data and isinstance(msg_data["content"], str):
                 sdk_history_to_init.append({
                    'role': msg_data['role'],
                    'parts': [{'text': msg_data['content']}]
                })
            elif "parts" in msg_data: 
                 sdk_history_to_init.append({
                    'role': msg_data['role'],
                    'parts': msg_data['parts']
                })

    if sdk_history_to_init:
        print(f"Creating session {session_id} with {len(sdk_history_to_init)} history entries.")
        session = client.chats.create(model="gemini-2.0-flash", history=sdk_history_to_init)
    else:
        print(f"Creating new empty session {session_id}.")
        session = client.chats.create(model="gemini-2.0-flash")
    
    chat_sessions[session_id] = session 
    return session

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
