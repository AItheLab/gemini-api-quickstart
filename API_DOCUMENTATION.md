# API de Gestión de Historial de Chats - Documentación

## Descripción General

Este sistema proporciona una API completa para gestionar conversaciones de chat con persistencia, metadatos avanzados y funcionalidades de búsqueda. El sistema ha sido mejorado para incluir:

- ✅ **Persistencia completa** del historial de chats
- ✅ **Metadatos avanzados** (títulos, etiquetas, fechas, contadores)
- ✅ **Búsqueda inteligente** en títulos y contenido
- ✅ **Organización** con etiquetas y chat fijados
- ✅ **Exportación** en múltiples formatos
- ✅ **Migración automática** desde el formato anterior

---

## Endpoints de la API

### 1. Gestión de Sesiones

#### `POST /sessions`
Crea una nueva sesión de chat.

**Response:**
```json
{
  \"success\": true,
  \"session_id\": \"uuid-string\"
}
```

---

### 2. Gestión de Mensajes

#### `POST /chat`
Envía un mensaje a una sesión específica.

**Headers:**
- `X-Session-ID`: ID de la sesión

**Body:**
```json
{
  \"message\": \"Tu mensaje aquí\"
}
```

#### `GET /stream?session_id=<id>`
Stream de respuesta en tiempo real del asistente.

**Parameters:**
- `session_id`: ID de la sesión

**Response:** Server-Sent Events stream

---

### 3. Historial de Conversaciones

#### `GET /sessions/<session_id>`
Obtiene el historial completo de una conversación.

**Response:**
```json
{
  \"success\": true,
  \"history\": [
    {
      \"role\": \"user\",
      \"content\": \"Mensaje del usuario\",
      \"timestamp\": 1735244400.0,
      \"message_id\": \"unique-id\"
    }
  ],
  \"metadata\": {
    \"title\": \"Título del chat\",
    \"created_at\": 1735244400.0,
    \"updated_at\": 1735244460.0,
    \"message_count\": 5,
    \"tags\": [\"importante\", \"trabajo\"],
    \"is_pinned\": false
  }
}
```

---

### 4. Lista y Búsqueda de Chats

#### `GET /chats`
Lista todos los chats con opciones de filtrado y búsqueda.

**Query Parameters:**
- `search`: Buscar por contenido o título
- `tag`: Filtrar por etiqueta específica
- `pinned`: Solo chats fijados (`true`/`false`)

**Ejemplos:**
```bash
# Listar todos los chats
GET /chats

# Buscar chats que contengan \"Python\"
GET /chats?search=Python

# Filtrar chats con etiqueta \"trabajo\"
GET /chats?tag=trabajo

# Solo chats fijados
GET /chats?pinned=true
```

**Response:**
```json
{
  \"success\": true,
  \"chats\": [
    {
      \"session_id\": \"uuid-string\",
      \"title\": \"Título del chat\",
      \"created_at\": 1735244400.0,
      \"updated_at\": 1735244460.0,
      \"message_count\": 5,
      \"last_message_preview\": \"Último mensaje...\",
      \"tags\": [\"importante\"],
      \"is_pinned\": false
    }
  ],
  \"total\": 1
}
```

---

### 5. Gestión de Metadatos

#### `PUT /chats/<session_id>`
Actualiza metadatos de un chat específico.

**Body Examples:**

**Cambiar título:**
```json
{
  \"title\": \"Nuevo título personalizado\"
}
```

**Alternar estado de fijado:**
```json
{
  \"toggle_pin\": true
}
```

**Gestionar etiquetas:**
```json
{
  \"add_tags\": [\"importante\", \"trabajo\"],
  \"remove_tags\": [\"antigua\"]
}
```

**Ejemplo combinado:**
```json
{
  \"title\": \"Chat de Programación Python\",
  \"add_tags\": [\"programación\", \"python\"],
  \"toggle_pin\": true
}
```

---

### 6. Eliminación de Chats

#### `DELETE /chats/<session_id>`
Elimina completamente un chat.

**Response:**
```json
{
  \"success\": true,
  \"message\": \"Chat deleted successfully\"
}
```

---

### 7. Exportación

#### `GET /chats/<session_id>/export?format=<format>`
Exporta un chat en el formato especificado.

**Parameters:**
- `format`: `json` o `txt`

**Ejemplos:**
```bash
# Exportar como JSON
GET /chats/uuid/export?format=json

# Exportar como texto plano
GET /chats/uuid/export?format=txt
```

**Response:** Archivo descargable en el formato solicitado.

---

### 8. Estadísticas

#### `GET /stats`
Obtiene estadísticas generales del sistema.

**Response:**
```json
{
  \"success\": true,
  \"stats\": {
    \"total_chats\": 25,
    \"total_messages\": 150,
    \"pinned_chats\": 3,
    \"recent_chats\": 8,
    \"all_tags\": [\"trabajo\", \"importante\", \"programación\"]
  }
}
```

---

### 9. Carga de Archivos

#### `POST /upload`
Sube una imagen para usar en la conversación.

**Headers:**
- `X-Session-ID`: ID de la sesión

**Form Data:**
- `file`: Archivo de imagen (PNG, JPG, JPEG)
- `message`: Mensaje opcional para acompañar la imagen

---

## Ejemplos de Uso

### JavaScript/Fetch API

```javascript
// Crear nueva sesión
const response = await fetch('/sessions', { method: 'POST' })
const { session_id } = await response.json()

// Enviar mensaje
await fetch('/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Session-ID': session_id
  },
  body: JSON.stringify({ message: 'Hola!' })
})

// Obtener historial
const history = await fetch(`/sessions/${session_id}`)
const chatData = await history.json()

// Buscar chats
const searchResults = await fetch('/chats?search=Python')
const { chats } = await searchResults.json()

// Actualizar metadatos
await fetch(`/chats/${session_id}`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    title: 'Mi Chat de Python',
    add_tags: ['programación', 'tutorial']
  })
})
```

### Python/Requests

```python
import requests

# Crear sesión
response = requests.post('http://localhost:5000/sessions')
session_id = response.json()['session_id']

# Enviar mensaje
requests.post('http://localhost:5000/chat', 
  json={'message': 'Hola!'}, 
  headers={'X-Session-ID': session_id}
)

# Buscar chats
search_response = requests.get('http://localhost:5000/chats', 
  params={'search': 'Python'}
)
chats = search_response.json()['chats']

# Exportar chat
export_response = requests.get(f'http://localhost:5000/chats/{session_id}/export',
  params={'format': 'txt'}
)
with open('chat_export.txt', 'w') as f:
    f.write(export_response.text)
```

---

## Estructura de Archivos

```
chat_histories/
├── metadata.json          # Metadatos de todos los chats
├── chats/                 # Directorio de mensajes individuales
│   ├── uuid1.json        # Mensajes del chat 1
│   └── uuid2.json        # Mensajes del chat 2
└── backup_old_format/     # Backup del formato anterior
    └── old_chat.json     # Archivos migrados
```

---

## Casos de Uso Comunes

### 1. **Dashboard de Chats**
```javascript
// Obtener chats recientes con vista previa
const chats = await fetch('/chats').then(r => r.json())
// Mostrar lista con títulos, fechas y previews
```

### 2. **Sistema de Búsqueda**
```javascript
// Búsqueda en tiempo real
const results = await fetch(`/chats?search=${query}`)
// Filtrar por etiquetas específicas
const workChats = await fetch('/chats?tag=trabajo')
```

### 3. **Organización Personal**
```javascript
// Fijar chats importantes
await fetch(`/chats/${id}`, {
  method: 'PUT',
  body: JSON.stringify({ toggle_pin: true })
})

// Categorizar con etiquetas
await fetch(`/chats/${id}`, {
  method: 'PUT', 
  body: JSON.stringify({ add_tags: ['proyecto-x', 'urgente'] })
})
```

### 4. **Backup y Exportación**
```javascript
// Exportar todo como JSON para backup
const allChats = await fetch('/chats').then(r => r.json())
for (const chat of allChats.chats) {
  const exportData = await fetch(`/chats/${chat.session_id}/export?format=json`)
  // Guardar exportData...
}
```

---

## Migración desde Formato Anterior

El sistema incluye migración automática. Los archivos del formato anterior se detectan y convierten automáticamente al arrancar el servidor. Los archivos originales se guardan en `backup_old_format/` por seguridad.

**Proceso de migración:**
1. ✅ Detección automática de archivos antiguos
2. ✅ Conversión al nuevo formato con timestamps
3. ✅ Generación automática de títulos
4. ✅ Backup de archivos originales
5. ✅ Creación de metadatos completos

---

## Códigos de Error

- `400`: Parámetros inválidos
- `404`: Chat no encontrado
- `500`: Error interno del servidor

Todos los errores incluyen un mensaje descriptivo en el campo `message` de la respuesta JSON.
