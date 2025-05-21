from fastapi import FastAPI, HTTPException, Request, Response, UploadFile, File, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from PIL import Image
import io
import os
import uuid
import asyncio
from dotenv import load_dotenv

from google import genai

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
    chat_sessions[session_id] = client.chats.create(model="gemini-2.0-flash")
    return {
        "success": True,
        "session_id": session_id
    }

@app.get("/api/sessions/{session_id}", response_model=HistoryResponse)
async def get_session(session_id: str):
    """Get the history of a chat session"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    history = []
    for message in chat_sessions[session_id].get_history():
        history.append({
            "role": message.role,
            "content": message.parts[0].text if message.parts else ""
        })
        
    return {
        "success": True,
        "history": history
    }

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Depends(get_session_id)
):
    """Upload an image file for multi-modal processing"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
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
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    pending_messages[session_id] = message_request.message
    
    return {"success": True}

@app.get("/api/stream")
async def stream(
    session_id: str = Depends(get_session_id_flexible)
):
    """Stream the AI response to a message"""
    print(f"Attempting to stream for session_id: {session_id}")
    
    if session_id not in chat_sessions:
        print(f"Session ID {session_id} not found in chat_sessions.")
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session_id not in pending_messages:
        print(f"Session ID {session_id} not found in pending_messages. Pending messages keys: {list(pending_messages.keys())}")
        raise HTTPException(status_code=400, detail="No pending message")
    
    print(f"Pending message found for session_id: {session_id}")
    # Prepare for streaming
    message = pending_messages[session_id]
    has_image = session_id in pending_images
    chat_session = chat_sessions[session_id]
    
    
    async def generate():
        # Handle multimodal or text-only message
        if has_image:
            image = pending_images[session_id]
            response = chat_session.send_message_stream([message, image])
            del pending_images[session_id]
        else:
            response = chat_session.send_message_stream(message)

        # Stream the response
        for chunk in response:
            yield f"data: {chunk.text}\n\n"
        
        # Signal end of stream
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
