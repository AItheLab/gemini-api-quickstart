from flask import (
    Flask,
    render_template,
    request,
    Response,
    stream_with_context,
    jsonify,
)
from werkzeug.utils import secure_filename
from PIL import Image
import io
from dotenv import load_dotenv
import os
import uuid
import time
from collections import defaultdict

from google import genai

# Load environment variables from .env file
load_dotenv()

# Create upload folder if it doesn't exist
os.makedirs('uploads', exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

# API client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Diccionario para mantener las sesiones de chat
# Clave: session_id, Valor: objeto de sesión de chat
chat_sessions = {}

# Diccionario para mensajes pendientes por sesión
# Clave: session_id, Valor: (next_message, next_image)
pending_messages = defaultdict(lambda: ("", ""))

# Tiempo de expiración de sesiones en segundos (2 horas)
SESSION_EXPIRY = 7200

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = 'uploads'


def allowed_file(filename):
    """Returns if a filename is supported via its extension"""
    _, ext = os.path.splitext(filename)
    return ext.lstrip('.').lower() in ALLOWED_EXTENSIONS

def get_session(session_id):
    """Obtiene una sesión existente o crea una nueva"""
    if session_id in chat_sessions:
        # Actualizar tiempo de último uso
        chat_sessions[session_id]["last_used"] = time.time()
        return chat_sessions[session_id]["session"]
    else:
        # Crear nueva sesión si no existe
        print(f"Creating new chat session for ID: {session_id}")
        session = client.chats.create(model="gemini-2.0-flash")
        chat_sessions[session_id] = {
            "session": session,
            "created_at": time.time(),
            "last_used": time.time()
        }
        return session

def clean_old_sessions():
    """Limpia sesiones antiguas para evitar consumo excesivo de memoria"""
    current_time = time.time()
    sessions_to_remove = []
    
    for session_id, session_data in chat_sessions.items():
        if current_time - session_data["last_used"] > SESSION_EXPIRY:
            sessions_to_remove.append(session_id)
    
    for session_id in sessions_to_remove:
        print(f"Removing expired session: {session_id}")
        del chat_sessions[session_id]
        if session_id in pending_messages:
            del pending_messages[session_id]


@app.route("/sessions", methods=["POST"])
def create_session():
    """Crea una nueva sesión de chat y devuelve su ID"""
    # Limpiar sesiones antiguas periódicamente
    clean_old_sessions()
    
    # Generar un nuevo ID de sesión
    session_id = str(uuid.uuid4())
    
    # Crear una nueva sesión
    get_session(session_id)
    
    return jsonify({
        "success": True,
        "session_id": session_id
    })

@app.route("/upload", methods=["POST"])
def upload_file():
    """Takes in a file, checks if it is valid,
    and saves it for the next request to the API
    """
    # Obtener session_id de los headers
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        return jsonify(success=False, message="No session ID provided")

    if "file" not in request.files:
        return jsonify(success=False, message="No file part")

    file = request.files["file"]
    message = request.form.get("message", "")

    if file.filename == "":
        return jsonify(success=False, message="No selected file")
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        # Read the file stream into a BytesIO object
        file_stream = io.BytesIO(file.read())
        file_stream.seek(0)
        img = Image.open(file_stream)
        
        # Guardar la imagen y el mensaje para la sesión específica
        next_msg = message.strip() if message.strip() else ""
        pending_messages[session_id] = (next_msg, img)

        return jsonify(
            success=True,
            message="File uploaded successfully and added to the conversation",
            filename=filename,
        )
    return jsonify(success=False, message="File type not allowed")


@app.route("/", methods=["GET"])
def index():
    """Renders the main homepage for the app"""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """
    Takes in the message the user wants to send
    to the Gemini API, saves it
    """
    # Obtener session_id de los headers
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        return jsonify(success=False, message="No session ID provided"), 400
    
    message = request.json.get("message", "")
    if not message.strip():
        return jsonify(success=False, message="Empty message"), 400
    
    try:
        # Verificar que la sesión existe o crearla
        get_session(session_id)
        
        # Guardar el mensaje para la sesión específica
        current_msg, current_img = pending_messages[session_id]
        
        # Si ya hay una imagen esperando, mantenerla; de lo contrario, usar solo el nuevo mensaje
        pending_messages[session_id] = (message, current_img)
        
        print(f"Message received for session {session_id}: {message}")
        print(f"Pending messages: {session_id} -> ({message}, {'image' if current_img else 'no image'})")
        
        return jsonify(success=True)
    except Exception as e:
        print(f"Error processing message for session {session_id}: {str(e)}")
        return jsonify(success=False, message=f"Error processing message: {str(e)}"), 500


@app.route("/sessions/<session_id>", methods=["GET"])
def get_history(session_id):
    """
    Returns the chat history for a specific session
    """
    if not session_id:
        return jsonify(success=False, message="No session ID provided")
    
    try:
        # Obtener o crear sesión
        session = get_session(session_id)
        
        # Obtener historial
        history = session.get_history()
        formatted_history = []
        
        for message in history:
            # Extraer el texto de las partes del mensaje
            text_content = ""
            if message.parts:
                for part in message.parts:
                    if hasattr(part, 'text') and part.text:
                        text_content += part.text
            
            formatted_history.append({
                "role": message.role,
                "content": text_content
            })
            
        return jsonify({
            "success": True,
            "history": formatted_history
        })
    except Exception as e:
        print(f"Error fetching history for session {session_id}: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error fetching history: {str(e)}"
        }), 404

@app.route("/stream", methods=["GET"])
def stream():
    """
    Streams the response from the server for
    both multi-modal and plain text requests
    """
    # Obtener el session_id como parámetro de consulta
    session_id = request.args.get("session_id")
    if not session_id:
        def error_generator():
            yield f"data: [Error: No session ID provided]\n\n"
        return Response(stream_with_context(error_generator),
                     mimetype="text/event-stream")
    
    # Print session state for debugging
    print(f"============== STREAM DEBUG ================")
    print(f"Session ID: {session_id}")
    print(f"Session exists in chat_sessions: {session_id in chat_sessions}")
    
    # Mostrar todos los mensajes pendientes para debug
    print(f"All pending messages:")
    for s_id, (msg, img) in pending_messages.items():
        print(f"  - {s_id}: Message: '{msg}', Has image: {img is not None and img != ''}")
    
    # Ver si hay mensaje pendiente para esta sesión    
    if session_id in pending_messages:
        message, image = pending_messages[session_id]
        print(f"Pending message for this session: '{message}', Has image: {image is not None and image != ''}")
    else:
        print(f"No pending message found for session {session_id}")
    print(f"===========================================")
    
    def generate():
        assistant_response_content = ""
        try:
            # Obtener la sesión
            session = get_session(session_id)
            
            # Obtener mensajes pendientes para esta sesión
            message, image = pending_messages[session_id]
            
            if not message.strip() and not image:
                error_msg = f"No pending message or image for session {session_id}"
                print(error_msg)
                yield f"data: [Error: {error_msg}]\n\n"
                return
            
            # Guardar una copia del mensaje antes de limpiarlo
            processing_message = message
            processing_image = image
            
            # Limpiar mensajes pendientes de esta sesión inmediatamente
            pending_messages[session_id] = ("", "")
            
            try:
                if processing_image:
                    print(f"Session {session_id}: Sending multimodal message...")
                    if processing_message.strip():
                        response = session.send_message_stream([processing_message, processing_image])
                    else:
                        response = session.send_message_stream([processing_image])
                else:
                    print(f"Session {session_id}: Sending text message: '{processing_message}'")
                    response = session.send_message_stream(processing_message)
                
                for chunk in response:
                    if hasattr(chunk, 'text') and chunk.text:
                        assistant_response_content += chunk.text
                        yield f"data: {chunk.text}\n\n"
            except Exception as e:
                error_str = str(e)
                print(f"Session {session_id}: Error exception: {error_str}")
                
                # Manejar errores específicos de forma más amigable
                if "503" in error_str and "overloaded" in error_str:
                    error_msg = "El modelo de IA está temporalmente sobrecargado. Por favor, espera un momento e intenta nuevamente."
                elif "UNAVAILABLE" in error_str:
                    error_msg = "El servicio de IA no está disponible en este momento. Por favor, intenta más tarde."
                else:
                    error_msg = f"Error al procesar el mensaje: {error_str}"
                
                print(f"Session {session_id}: Sending friendly error: {error_msg}")
                yield f"data: [Error: {error_msg}]\n\n"
                
        except Exception as e:
            error_msg = f"General error in stream generation: {str(e)}"
            print(f"Session {session_id}: {error_msg}")
            yield f"data: [Error: {error_msg}]\n\n"

    return Response(stream_with_context(generate()),
                    mimetype="text/event-stream", 
                    headers={
                        'Cache-Control': 'no-cache',
                        'X-Accel-Buffering': 'no'
                    })
