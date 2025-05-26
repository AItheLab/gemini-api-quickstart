"""
Sistema de Gestión de Historial de Chats Mejorado
Proporciona persistencia, metadatos y funcionalidades avanzadas para el historial de chats.
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import re
from google import genai


@dataclass
class ChatMessage:
    """Representa un mensaje individual en el chat"""
    role: str  # 'user' o 'model'
    content: str
    timestamp: float
    message_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        return cls(**data)


@dataclass
class ChatMetadata:
    """Metadatos del chat para mejor organización y búsqueda"""
    session_id: str
    title: str
    created_at: float
    updated_at: float
    message_count: int
    last_message_preview: str
    tags: List[str]
    is_pinned: bool = False
    custom_title: Optional[str] = None  # Título personalizado por el usuario
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMetadata':
        return cls(**data)


class ChatHistoryManager:
    """Gestor principal del historial de chats con persistencia y funcionalidades avanzadas"""
    
    def __init__(self, base_dir: str = "chat_histories"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Archivos principales
        self.metadata_file = self.base_dir / "metadata.json"
        self.chats_dir = self.base_dir / "chats"
        self.chats_dir.mkdir(exist_ok=True)
        
        # Cache en memoria para mejor rendimiento
        self._metadata_cache: Dict[str, ChatMetadata] = {}
        self._load_metadata()
    
    def _load_metadata(self):
        """Carga los metadatos desde el archivo"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._metadata_cache = {
                        session_id: ChatMetadata.from_dict(meta_data)
                        for session_id, meta_data in data.items()
                    }
                print(f"Cargados {len(self._metadata_cache)} metadatos de chat")
            except Exception as e:
                print(f"Error cargando metadatos: {e}")
                self._metadata_cache = {}
        else:
            self._metadata_cache = {}
    
    def _save_metadata(self):
        """Guarda los metadatos en el archivo"""
        try:
            data = {
                session_id: metadata.to_dict()
                for session_id, metadata in self._metadata_cache.items()
            }
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando metadatos: {e}")
    
    def _get_chat_file(self, session_id: str) -> Path:
        """Obtiene la ruta del archivo de chat"""
        return self.chats_dir / f"{session_id}.json"
    
    def _generate_auto_title(self, messages: List[ChatMessage], client: Optional[Any] = None) -> str:
        """Genera un título automático basado en los primeros mensajes"""
        if not messages:
            return "Chat vacío"
        
        # Obtener el primer mensaje del usuario
        user_messages = [msg for msg in messages if msg.role == 'user']
        if not user_messages:
            return "Nuevo chat"
        
        first_message = user_messages[0].content.strip()
        
        # Si hay un cliente Gemini disponible, intentar generar título con IA
        if client and len(first_message) > 20:
            try:
                prompt = f"""Genera un título conciso y descriptivo (máximo 50 caracteres) para un chat que comenzó con este mensaje:

"{first_message[:200]}"

Responde solo con el título, sin comillas ni explicaciones."""
                
                # Crear una sesión temporal para generar el título
                temp_session = client.chats.create(model="gemini-2.0-flash")
                response = temp_session.send_message(prompt)
                
                if response and hasattr(response, 'text') and response.text:
                    title = response.text.strip().replace('"', '').replace("'", "")
                    if len(title) <= 50 and title:
                        return title
            except Exception as e:
                print(f"Error generando título automático: {e}")
        
        # Fallback: usar el primer mensaje truncado
        if len(first_message) <= 40:
            return first_message
        else:
            return first_message[:37] + "..."
    
    def create_chat(self, session_id: str, client: Optional[Any] = None) -> ChatMetadata:
        """Crea un nuevo chat con metadatos iniciales"""
        current_time = time.time()
        
        metadata = ChatMetadata(
            session_id=session_id,
            title="Nuevo chat",
            created_at=current_time,
            updated_at=current_time,
            message_count=0,
            last_message_preview="",
            tags=[]
        )
        
        self._metadata_cache[session_id] = metadata
        self._save_metadata()
        
        # Crear archivo de chat vacío
        self._save_chat_messages(session_id, [])
        
        print(f"Chat creado: {session_id}")
        return metadata
    
    def add_message(self, session_id: str, role: str, content: str, client: Optional[Any] = None) -> ChatMessage:
        """Añade un mensaje al chat y actualiza metadatos"""
        current_time = time.time()
        message_id = f"{session_id}_{int(current_time * 1000)}"
        
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=current_time,
            message_id=message_id
        )
        
        # Cargar mensajes existentes
        messages = self.get_chat_messages(session_id)
        messages.append(message)
        
        # Guardar mensajes actualizados
        self._save_chat_messages(session_id, messages)
        
        # Actualizar metadatos
        if session_id not in self._metadata_cache:
            self.create_chat(session_id, client)
        
        metadata = self._metadata_cache[session_id]
        metadata.message_count = len(messages)
        metadata.updated_at = current_time
        metadata.last_message_preview = content[:100] + "..." if len(content) > 100 else content
        
        # Actualizar título si es el primer mensaje significativo
        if metadata.title == "Nuevo chat" and role == 'user' and content.strip():
            metadata.title = self._generate_auto_title(messages, client)
        
        self._save_metadata()
        
        print(f"Mensaje añadido al chat {session_id}: {role}")
        return message
    
    def get_chat_messages(self, session_id: str) -> List[ChatMessage]:
        """Obtiene todos los mensajes de un chat"""
        chat_file = self._get_chat_file(session_id)
        
        if not chat_file.exists():
            return []
        
        try:
            with open(chat_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [ChatMessage.from_dict(msg_data) for msg_data in data]
        except Exception as e:
            print(f"Error cargando mensajes del chat {session_id}: {e}")
            return []
    
    def _save_chat_messages(self, session_id: str, messages: List[ChatMessage]):
        """Guarda los mensajes de un chat"""
        chat_file = self._get_chat_file(session_id)
        
        try:
            data = [message.to_dict() for message in messages]
            with open(chat_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando mensajes del chat {session_id}: {e}")
    
    def get_all_chats_metadata(self) -> List[ChatMetadata]:
        """Obtiene metadatos de todos los chats ordenados por fecha de actualización"""
        return sorted(
            self._metadata_cache.values(),
            key=lambda x: x.updated_at,
            reverse=True
        )
    
    def get_chat_metadata(self, session_id: str) -> Optional[ChatMetadata]:
        """Obtiene los metadatos de un chat específico"""
        return self._metadata_cache.get(session_id)
    
    def update_chat_title(self, session_id: str, new_title: str):
        """Actualiza el título de un chat"""
        if session_id in self._metadata_cache:
            self._metadata_cache[session_id].custom_title = new_title
            self._metadata_cache[session_id].updated_at = time.time()
            self._save_metadata()
    
    def toggle_pin_chat(self, session_id: str):
        """Alterna el estado de pin de un chat"""
        if session_id in self._metadata_cache:
            metadata = self._metadata_cache[session_id]
            metadata.is_pinned = not metadata.is_pinned
            metadata.updated_at = time.time()
            self._save_metadata()
    
    def add_tag_to_chat(self, session_id: str, tag: str):
        """Añade una etiqueta a un chat"""
        if session_id in self._metadata_cache:
            metadata = self._metadata_cache[session_id]
            if tag not in metadata.tags:
                metadata.tags.append(tag)
                metadata.updated_at = time.time()
                self._save_metadata()
    
    def remove_tag_from_chat(self, session_id: str, tag: str):
        """Elimina una etiqueta de un chat"""
        if session_id in self._metadata_cache:
            metadata = self._metadata_cache[session_id]
            if tag in metadata.tags:
                metadata.tags.remove(tag)
                metadata.updated_at = time.time()
                self._save_metadata()
    
    def search_chats(self, query: str, search_in_content: bool = True) -> List[ChatMetadata]:
        """Busca chats por título, contenido o etiquetas"""
        query_lower = query.lower()
        results = []
        
        for metadata in self._metadata_cache.values():
            # Buscar en título
            title_to_search = metadata.custom_title or metadata.title
            if query_lower in title_to_search.lower():
                results.append(metadata)
                continue
            
            # Buscar en etiquetas
            if any(query_lower in tag.lower() for tag in metadata.tags):
                results.append(metadata)
                continue
            
            # Buscar en preview del último mensaje
            if query_lower in metadata.last_message_preview.lower():
                results.append(metadata)
                continue
            
            # Buscar en contenido completo si se solicita
            if search_in_content:
                messages = self.get_chat_messages(metadata.session_id)
                if any(query_lower in msg.content.lower() for msg in messages):
                    results.append(metadata)
        
        return sorted(results, key=lambda x: x.updated_at, reverse=True)
    
    def delete_chat(self, session_id: str):
        """Elimina un chat completamente"""
        # Eliminar archivo de mensajes
        chat_file = self._get_chat_file(session_id)
        if chat_file.exists():
            chat_file.unlink()
        
        # Eliminar de metadatos
        if session_id in self._metadata_cache:
            del self._metadata_cache[session_id]
            self._save_metadata()
        
        print(f"Chat eliminado: {session_id}")
    
    def export_chat(self, session_id: str, format_type: str = "json") -> Optional[str]:
        """Exporta un chat en el formato especificado"""
        metadata = self.get_chat_metadata(session_id)
        messages = self.get_chat_messages(session_id)
        
        if not metadata or not messages:
            return None
        
        export_data = {
            "metadata": metadata.to_dict(),
            "messages": [msg.to_dict() for msg in messages],
            "exported_at": time.time()
        }
        
        if format_type == "json":
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        elif format_type == "txt":
            lines = [f"Chat: {metadata.custom_title or metadata.title}"]
            lines.append(f"Creado: {datetime.fromtimestamp(metadata.created_at)}")
            lines.append(f"Mensajes: {metadata.message_count}")
            lines.append("-" * 50)
            
            for msg in messages:
                timestamp = datetime.fromtimestamp(msg.timestamp).strftime("%Y-%m-%d %H:%M")
                role_label = "Usuario" if msg.role == "user" else "Asistente"
                lines.append(f"\n[{timestamp}] {role_label}:")
                lines.append(msg.content)
            
            return "\n".join(lines)
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales del historial"""
        total_chats = len(self._metadata_cache)
        total_messages = sum(meta.message_count for meta in self._metadata_cache.values())
        pinned_chats = sum(1 for meta in self._metadata_cache.values() if meta.is_pinned)
        
        # Chats por día (últimos 30 días)
        now = time.time()
        thirty_days_ago = now - (30 * 24 * 60 * 60)
        recent_chats = [
            meta for meta in self._metadata_cache.values()
            if meta.created_at >= thirty_days_ago
        ]
        
        return {
            "total_chats": total_chats,
            "total_messages": total_messages,
            "pinned_chats": pinned_chats,
            "recent_chats": len(recent_chats),
            "all_tags": list(set(tag for meta in self._metadata_cache.values() for tag in meta.tags))
        }

