# 🤖 Gemini Chat API con Historial Inteligente

Una aplicación completa de chat con IA utilizando la API de Gemini de Google, featuring un sistema avanzado de gestión de historial con persistencia, metadatos y búsqueda inteligente.

## ✨ Características Principales

### 🧠 **IA Conversacional**
- Integración completa con Gemini 2.0 Flash
- Soporte multimodal (texto + imágenes)
- Streaming de respuestas en tiempo real
- Gestión inteligente de sesiones

### 💾 **Historial Persistente Avanzado**
- ✅ **Persistencia completa** - No perder nunca una conversación
- ✅ **Metadatos inteligentes** - Títulos automáticos, fechas, contadores
- ✅ **Sistema de etiquetas** - Organiza tus chats por temas
- ✅ **Chats fijados** - Marca conversaciones importantes
- ✅ **Búsqueda potente** - Busca en títulos y contenido completo
- ✅ **Exportación múltiple** - JSON y texto plano
- ✅ **Migración automática** - Actualización sin pérdida de datos

### 🔍 **Gestión y Organización**
- Dashboard de chats con vista previa
- Filtrado por etiquetas y estado
- Estadísticas del uso del sistema
- Títulos generados automáticamente con IA
- Timestamps precisos para cada mensaje

## 🚀 Inicio Rápido

### 1. **Configuración del Entorno**
```bash
# Clonar el repositorio
git clone <repo-url>
cd gemini-api-quickstart

# Crear archivo .env con tu clave API
echo \"GOOGLE_API_KEY=tu_clave_aqui\" > .env
```

### 2. **Opción A: Docker (Recomendado)**
```bash
# Iniciar toda la aplicación
docker-compose up --build

# Acceder a:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - Documentación: http://localhost:8000/docs
```

### 3. **Opción B: Desarrollo Local**
```bash
# Backend Python
pip install -r requirements.txt
python app.py

# Frontend (en otra terminal)
cd frontend
npm install
npm run dev
```

## 📁 Estructura del Proyecto

```
gemini-api-quickstart/
├── 🐍 Backend Python Flask
│   ├── app.py                 # Servidor principal con API completa
│   ├── chat_manager.py        # Sistema de historial avanzado
│   ├── migrate_chat_history.py # Script de migración
│   └── test_api.py           # Suite de pruebas automatizadas
│
├── 📊 Sistema de Historial
│   └── chat_histories/
│       ├── metadata.json      # Metadatos de todos los chats
│       ├── chats/            # Mensajes individuales
│       └── backup_old_format/ # Backup de migraciones
│
├── 🎨 Frontend (Si existe)
│   └── frontend/
│
├── 📋 Documentación
│   ├── README.md             # Esta guía
│   ├── API_DOCUMENTATION.md  # Documentación completa de API
│   └── requirements.txt      # Dependencias Python
│
└── 🐳 Docker
    ├── Dockerfile
    ├── docker-compose.yml
    └── docker-compose.dev.yml
```

## 🛠️ API Endpoints

### **Gestión de Sesiones**
- `POST /sessions` - Crear nueva sesión
- `GET /sessions/{id}` - Obtener historial completo

### **Conversación**
- `POST /chat` - Enviar mensaje
- `GET /stream` - Recibir respuestas en streaming
- `POST /upload` - Subir imágenes

### **Gestión de Historial** ⭐ *NUEVO*
- `GET /chats` - Listar todos los chats con filtros
- `PUT /chats/{id}` - Actualizar metadatos (título, etiquetas, pin)
- `DELETE /chats/{id}` - Eliminar chat
- `GET /chats/{id}/export` - Exportar chat (JSON/TXT)

### **Búsqueda y Estadísticas** ⭐ *NUEVO*
- `GET /chats?search=query` - Buscar en chats
- `GET /chats?tag=etiqueta` - Filtrar por etiqueta
- `GET /chats?pinned=true` - Solo chats fijados
- `GET /stats` - Estadísticas del sistema

## 💡 Ejemplos de Uso

### **Búsqueda Inteligente**
```bash
# Buscar conversaciones sobre Python
curl \"http://localhost:5000/chats?search=Python\"

# Filtrar chats de trabajo
curl \"http://localhost:5000/chats?tag=trabajo\"

# Solo chats importantes (fijados)
curl \"http://localhost:5000/chats?pinned=true\"
```

### **Gestión de Metadatos**
```bash
# Cambiar título y añadir etiquetas
curl -X PUT \"http://localhost:5000/chats/{session_id}\" \\
  -H \"Content-Type: application/json\" \\
  -d '{
    \"title\": \"Chat de Programación Python\",
    \"add_tags\": [\"python\", \"programación\", \"tutorial\"],
    \"toggle_pin\": true
  }'
```

### **Exportación**
```bash
# Exportar como JSON
curl \"http://localhost:5000/chats/{session_id}/export?format=json\" > chat.json

# Exportar como texto
curl \"http://localhost:5000/chats/{session_id}/export?format=txt\" > chat.txt
```

## 🧪 Pruebas Automatizadas

Ejecuta la suite completa de pruebas:

```bash
# Asegúrate de que el servidor esté corriendo
python app.py &

# Ejecutar pruebas
python test_api.py

# Ver reporte detallado
cat test_report.json
```

Las pruebas verifican:
- ✅ Creación de sesiones
- ✅ Envío de mensajes
- ✅ Obtención de historial
- ✅ Búsqueda y filtrado
- ✅ Gestión de metadatos
- ✅ Exportación de datos
- ✅ Estadísticas del sistema

## 🔧 Configuración Avanzada

### **Variables de Entorno**
```env
GOOGLE_API_KEY=tu_clave_gemini_aqui
FLASK_ENV=development  # o production
CHAT_HISTORY_DIR=chat_histories  # directorio personalizado
SESSION_EXPIRY=7200  # segundos (2 horas)
```

### **Personalización del Historial**
```python
# En chat_manager.py puedes modificar:
- Generación automática de títulos
- Estructura de metadatos
- Políticas de limpieza automática
- Formatos de exportación
```

## 📈 Migración desde Versiones Anteriores

El sistema incluye migración automática:

1. **Detección automática** de archivos antiguos
2. **Conversión segura** al nuevo formato
3. **Backup automático** de datos originales
4. **Generación de metadatos** completos

```bash
# Migración manual si es necesaria
python migrate_chat_history.py
```

## 🎯 Casos de Uso

### **Dashboard Personal**
- Lista de chats recientes con previews
- Organización por etiquetas (trabajo, personal, aprendizaje)
- Búsqueda rápida en conversaciones históricas

### **Gestión de Proyectos**
- Chats fijados para proyectos importantes
- Etiquetas para categorización automática
- Exportación para documentación

### **Aprendizaje y Desarrollo**
- Historial de tutoriales y explicaciones
- Búsqueda en conocimientos adquiridos
- Backup y portabilidad de aprendizajes

## 🚨 Troubleshooting

### **Problemas Comunes**

**Error: \"No session ID provided\"**
```bash
# Asegúrate de incluir el header X-Session-ID
curl -H \"X-Session-ID: your-session-id\" ...
```

**Error: \"Chat not found\"**
```bash
# Verifica que el session_id existe
curl \"http://localhost:5000/chats\" | jq '.chats[].session_id'
```

**Migración no funcionando**
```bash
# Ejecuta manualmente la migración
python migrate_chat_history.py
```

### **Logs de Debug**
El sistema imprime logs detallados en la consola. Para mayor verbosidad:
```python
# En app.py, añadir al inicio:
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📄 Documentación Adicional

- 📖 **[API Documentation](./API_DOCUMENTATION.md)** - Documentación completa de endpoints
- 🧪 **[Test Report](./test_report.json)** - Resultados de pruebas automatizadas
- 🔄 **[Migration Script](./migrate_chat_history.py)** - Script de migración de datos

## 📜 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

---

**🎉 ¡Disfruta chateando con IA y nunca pierdas una conversación importante!**
