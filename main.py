from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, AsyncGenerator

from PIL import Image
import io
import os
import uuid
import json
from pathlib import Path
import aiofiles
from dotenv import load_dotenv
import traceback 

from google import genai
from google.genai import types as genai_types

from tools.tool_registry import get_available_tools_for_sdk, get_tool_implementation

load_dotenv()

GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set.")

MODEL_NAME = "gemini-2.0-flash" 

app = FastAPI(
    title="Gemini API Server (google-genai SDK)",
    description="API server for Gemini interactions using google-genai SDK",
    version="1.2.0" # Versión Limpia
)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

chat_histories: Dict[str, List[genai_types.Content]] = {}
pending_messages: Dict[str, str] = {}
pending_images: Dict[str, Image.Image] = {} 

CHAT_HISTORY_DIR = Path("chat_histories")
CHAT_HISTORY_DIR.mkdir(parents=True, exist_ok=True)

class MessageRequest(BaseModel): message: str
class SessionResponse(BaseModel): success: bool; session_id: str
class MessageResponse(BaseModel): success: bool
class HistoryItem(BaseModel): role: str; content: str 
class HistoryResponse(BaseModel): success: bool; history: List[HistoryItem]

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

async def get_session_id(x_session_id: str = Header(...)):
    if not x_session_id: raise HTTPException(status_code=400, detail="Missing session ID")
    return x_session_id

async def get_session_id_flexible(
    x_session_id: Optional[str] = Header(None), session_id: Optional[str] = Query(None)
):
    effective_session_id = x_session_id or session_id
    if not effective_session_id: raise HTTPException(status_code=400, detail="Missing session ID")
    return effective_session_id

def _sdk_history_to_api_history(sdk_history: List[genai_types.Content]) -> List[HistoryItem]:
    api_history = []
    for content_obj in sdk_history:
        role = content_obj.role if content_obj.role else "user"
        
        # Solo nos interesan los roles 'user' y 'model' para la visualización del chat del usuario final.
        # El rol 'function' es interno para el modelo.
        if role == "user":
            # Para el usuario, asumimos que la primera parte de texto es el mensaje principal.
            text_content = ""
            if content_obj.parts:
                # Buscar la primera parte de texto. Si hay imágenes, se ignoran aquí para la representación simple.
                for part in content_obj.parts:
                    if hasattr(part, 'text') and part.text is not None:
                        text_content = part.text
                        break
            if text_content: # Solo añadir si hay contenido de texto
                api_history.append(HistoryItem(role="user", content=text_content))

        elif role == "model":
            # Para el modelo, queremos el texto visible, no las FunctionCall.
            # Las FunctionCall son seguidas por una FunctionResponse y luego más texto del modelo.
            # Si una 'Content' de 'model' solo contiene una FunctionCall, la omitimos para el frontend.
            # Si contiene texto, lo tomamos.
            text_parts_for_model = []
            contains_only_function_call = False
            if len(content_obj.parts) == 1 and hasattr(content_obj.parts[0], 'function_call'):
                contains_only_function_call = True
            
            if not contains_only_function_call:
                for part in content_obj.parts:
                    if hasattr(part, 'text') and part.text is not None:
                        text_parts_for_model.append(part.text)
                
                full_text = " ".join(text_parts_for_model).strip()
                if full_text: # Solo añadir si hay contenido de texto
                    api_history.append(HistoryItem(role="model", content=full_text))
        
        # Los roles 'function' (FunctionResponse) se omiten para la visualización del chat del usuario.
        # El historial completo (incluyendo 'function' y FC en 'model') se mantiene en `current_sdk_history`
        # y se guarda en el archivo `session_id.json` para la lógica interna del modelo.

    return api_history

def _api_history_to_sdk_history(api_history: List[Dict[str, Any]]) -> List[genai_types.Content]:
    sdk_history = []
    for item in api_history:
        role = item.get('role', 'user')
        text = item.get('content', '')
        if text: 
             sdk_history.append(genai_types.Content(role=role, parts=[genai_types.Part.from_text(text=text)]))
    return sdk_history

async def load_chat_history_from_file(session_id: str) -> List[genai_types.Content]:
    filepath = CHAT_HISTORY_DIR / f"{session_id}.json"
    if not filepath.exists(): return []
    try:
        async with aiofiles.open(filepath, "r") as f:
            content_json = await f.read()
            api_history_dicts: List[Dict[str, Any]] = json.loads(content_json)
            return _api_history_to_sdk_history(api_history_dicts)
    except Exception as e:
        print(f"Error loading history for session {session_id}: {e}")
        return []

async def save_chat_history_to_file(session_id: str, sdk_history: List[genai_types.Content]):
    filepath = CHAT_HISTORY_DIR / f"{session_id}.json"
    try:
        api_history_items = _sdk_history_to_api_history(sdk_history) 
        history_to_save = [item.model_dump() for item in api_history_items] 
        async with aiofiles.open(filepath, "w") as f:
            await f.write(json.dumps(history_to_save, indent=2))
        # print(f"DEBUG: History saved for session {session_id}") # Comentado
    except Exception as e:
        print(f"Error saving history for session {session_id}: {e}")

async def _get_or_create_chat_history(session_id: str) -> List[genai_types.Content]:
    if session_id not in chat_histories:
        # print(f"DEBUG: Loading history for new/existing session {session_id} from file.") # Comentado
        chat_histories[session_id] = await load_chat_history_from_file(session_id)
    return chat_histories[session_id]

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session_endpoint_v2(): 
    session_id = str(uuid.uuid4())
    await _get_or_create_chat_history(session_id) 
    # print(f"DEBUG: Session created: {session_id}") # Comentado
    return SessionResponse(success=True, session_id=session_id)

@app.get("/api/sessions/{session_id}", response_model=HistoryResponse)
async def get_session_history_v2(session_id: str): 
    sdk_history = await _get_or_create_chat_history(session_id)
    api_history = _sdk_history_to_api_history(sdk_history)
    # print(f"DEBUG: Getting history for session {session_id}, {len(api_history)} items.") # Comentado
    return HistoryResponse(success=True, history=api_history)

@app.post("/api/upload")
async def upload_file_endpoint_v2( 
    file: UploadFile = File(...),
    session_id: str = Depends(get_session_id)
):
    if not file.filename or not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="File type not allowed or no file provided")
    contents = await file.read()
    try:
        pending_images[session_id] = Image.open(io.BytesIO(contents))
        # print(f"DEBUG: Image uploaded for session {session_id}: {file.filename}") # Comentado
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
    return {"success": True, "message": "File uploaded successfully", "filename": file.filename}

@app.post("/api/chat", response_model=MessageResponse)
async def chat_endpoint_v2( 
    message_request: MessageRequest,
    session_id: str = Depends(get_session_id)
):
    pending_messages[session_id] = message_request.message
    # print(f"DEBUG: Message received for session {session_id}: \"{message_request.message}\"") # Comentado
    return MessageResponse(success=True)

@app.get("/api/stream")
async def stream_endpoint_v2(session_id: str = Depends(get_session_id_flexible)): 
    gemini_client = genai.Client(api_key=GEMINI_API_KEY) 
    current_sdk_history = await _get_or_create_chat_history(session_id)
    
    user_text = pending_messages.pop(session_id, "")
    user_image = pending_images.pop(session_id, None)

    if not user_text and not user_image:
        async def no_content_stream():
            yield "data: [Error: No hay contenido (texto o imagen) para enviar.]\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(no_content_stream(), media_type="text/event-stream")

    user_parts = []
    if user_text:
        user_parts.append(genai_types.Part.from_text(text=user_text))
    if user_image:
        user_parts.append(user_image)
    
    if not user_parts: 
        async def empty_parts_stream():
            yield "data: [Error: No se pueden enviar partes de mensaje vacías.]\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(empty_parts_stream(), media_type="text/event-stream")

    current_sdk_history.append(genai_types.Content(role="user", parts=user_parts))
    # print(f"DEBUG: User message added. History length for session {session_id}: {len(current_sdk_history)}") # Comentado
    
    tools_config = get_available_tools_for_sdk()
    generate_config = genai_types.GenerateContentConfig(
        tools=tools_config,
    )

    async def generate_response_from_gemini() -> AsyncGenerator[str, None]:
        nonlocal current_sdk_history
        final_done_sent = False
        
        try:
            # print(f"--- Turno para Sesión {session_id} ---") # Comentado
            stream_chunks = gemini_client.models.generate_content_stream(
                model=MODEL_NAME,
                contents=current_sdk_history,
                config=generate_config,
            )
            
            accumulated_model_parts_for_current_turn = []
            function_call_to_execute = None

            # print("DEBUG: Esperando respuesta del modelo (puede incluir FC)...") # Comentado
            for chunk in stream_chunks:
                if hasattr(chunk, 'text') and chunk.text:
                    # print(f"DEBUG: Texto del modelo (chunk): \"{chunk.text}\"") # Comentado
                    yield f"data: {chunk.text}\n\n"
                    accumulated_model_parts_for_current_turn.append(genai_types.Part.from_text(text=chunk.text))
                
                if not function_call_to_execute and hasattr(chunk, 'candidates') and chunk.candidates:
                    candidate = chunk.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part_idx, part in enumerate(candidate.content.parts):
                            if hasattr(part, 'function_call') and part.function_call:
                                function_call_to_execute = part.function_call
                                accumulated_model_parts_for_current_turn.append(part)
                                # print(f"DEBUG: LLAMADA DE FUNCIÓN DETECTADA (via chunk.candidates): {function_call_to_execute.name}") # Comentado
                                break 
                
                if not function_call_to_execute and hasattr(chunk, 'parts'): 
                    for part_idx, part in enumerate(chunk.parts):
                        if hasattr(part, 'function_call') and part.function_call:
                            function_call_to_execute = part.function_call
                            accumulated_model_parts_for_current_turn.append(part)
                            # print(f"DEBUG: LLAMADA DE FUNCIÓN DETECTADA (via chunk.parts): {function_call_to_execute.name}") # Comentado
                            break 
                
                if function_call_to_execute:
                    # print("DEBUG: FunctionCall detectada, saliendo del bucle de chunks para procesarla.") # Comentado
                    break 

            if accumulated_model_parts_for_current_turn:
                current_sdk_history.append(genai_types.Content(role="model", parts=accumulated_model_parts_for_current_turn))
                # print(f"DEBUG: Historial actualizado con respuesta del modelo (FC o texto). Longitud: {len(current_sdk_history)}") # Comentado

            if function_call_to_execute:
                # ELIMINADO: yield f"data: [INFO: Usando herramienta {function_call_to_execute.name}...]\n\n" 
                
                tool_name = function_call_to_execute.name
                tool_args = dict(function_call_to_execute.args)
                
                # print(f"DEBUG: Ejecutando herramienta '{tool_name}' con argumentos: {tool_args}") # Comentado
                tool_function = get_tool_implementation(tool_name)

                if tool_function:
                    try:
                        tool_output = tool_function(**tool_args)
                        # print(f"DEBUG: Herramienta '{tool_name}' ejecutada. Salida: {tool_output}") # Comentado

                        function_response_part = genai_types.Part.from_function_response(
                            name=tool_name,
                            response={"content": tool_output}
                        )
                        current_sdk_history.append(genai_types.Content(role="function", parts=[function_response_part]))
                        # print(f"DEBUG: Historial actualizado con respuesta de función. Longitud: {len(current_sdk_history)}") # Comentado

                        # print("DEBUG: Volviendo a llamar al modelo con la respuesta de la herramienta...") # Comentado
                        final_stream_chunks = gemini_client.models.generate_content_stream(
                            model=MODEL_NAME,
                            contents=current_sdk_history,
                            config=generate_config,
                        )
                        
                        final_model_response_parts_after_tool = []
                        text_received_after_tool = False
                        for final_chunk in final_stream_chunks:
                            if hasattr(final_chunk, 'text') and final_chunk.text:
                                text_received_after_tool = True
                                # print(f"DEBUG: Texto del modelo (post-herramienta): \"{final_chunk.text}\"") # Comentado
                                yield f"data: {final_chunk.text}\n\n"
                                final_model_response_parts_after_tool.append(genai_types.Part.from_text(text=final_chunk.text))
                        
                        if not text_received_after_tool:
                             print(f"WARN: No se recibió texto del modelo después de la ejecución de la herramienta '{tool_name}'.") # Dejado como WARN
                             # ELIMINADO: yield "data: [INFO: La herramienta se ejecutó, pero el modelo no proporcionó más texto.]\n\n"

                        if final_model_response_parts_after_tool:
                            current_sdk_history.append(genai_types.Content(role="model", parts=final_model_response_parts_after_tool))
                            # print(f"DEBUG: Historial actualizado con respuesta final del modelo. Longitud: {len(current_sdk_history)}") # Comentado

                    except Exception as e_tool:
                        error_msg = f"[Error al ejecutar la herramienta '{tool_name}': {str(e_tool)}]"
                        print(f"ERROR: {error_msg}") # Dejado como ERROR
                        yield f"data: {error_msg}\n\n"
                        current_sdk_history.append(genai_types.Content(role="model", parts=[genai_types.Part.from_text(text=error_msg)]))
                else: 
                    error_msg = f"[Error: Herramienta '{tool_name}' no implementada en el backend]"
                    print(f"ERROR: {error_msg}") # Dejado como ERROR
                    yield f"data: {error_msg}\n\n"
                    current_sdk_history.append(genai_types.Content(role="model", parts=[genai_types.Part.from_text(text=error_msg)]))
            
            await save_chat_history_to_file(session_id, current_sdk_history)

        except Exception as e:
            print(f"ERROR FATAL en generate_response_from_gemini para sesión {session_id}:")
            traceback.print_exc()
            try: 
                yield f"data: [Error crítico en el servidor: Consulte los logs del backend. {str(e)}]\n\n"
            except Exception:
                pass
        finally:
            if not final_done_sent:
                # print(f"DEBUG: Enviando [DONE] para sesión {session_id}") # Comentado
                yield "data: [DONE]\n\n"
                final_done_sent = True
                
    return StreamingResponse(generate_response_from_gemini(), media_type="text/event-stream")

@app.get("/api/health")
async def health_check_v2(): return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)