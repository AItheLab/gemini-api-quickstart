# Gemini API Modern Stack

Esta aplicación utiliza la API de Gemini de Google para crear una experiencia interactiva de chat con inteligencia artificial. El proyecto cuenta con un backend API basado en FastAPI y un frontend moderno con Vue 3.

## Estructura del Proyecto

```
gemini-api-quickstart/
├── main.py               # Backend FastAPI
├── requirements.txt      # Dependencias Python
├── Dockerfile           # Configuración de Docker para el backend
├── docker-compose.yml   # Configuración para producción
├── docker-compose.dev.yml # Configuración para desarrollo
└── frontend/            # Frontend Vue 3 + Vite + TypeScript + Tailwind
```

## Configuración Rápida

1. **Crear archivo `.env`** con tu clave API de Gemini:
   ```
   GOOGLE_API_KEY=tu_clave_aqui
   ```

2. **Iniciar la aplicación completa con Docker**:
   ```bash
   docker-compose up --build
   ```

   La aplicación estará disponible en:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Documentación API: http://localhost:8000/docs

3. **Para detener la aplicación**:
   ```bash
   docker-compose down
   ```

## Modo Desarrollo

Para desarrollo con hot-reload tanto en el frontend como en el backend:

```bash
docker-compose -f docker-compose.dev.yml up --build
```

## Características

- **Backend FastAPI** con soporte para:
  - Sesiones de chat persistentes
  - Procesamiento de imágenes (multimodal)
  - Streaming de respuestas en tiempo real
  - Documentación OpenAPI automática

- **Frontend Vue 3 + Vite** con:
  - TypeScript para tipo seguro
  - Tailwind CSS para estilos
  - Interfaz de chat moderna y responsive
  - Soporte para carga de imágenes
  - Visualización de respuestas en streaming

## API Endpoints

- `POST /api/sessions` - Crear nueva sesión de chat
- `GET /api/sessions/{session_id}` - Obtener historial de sesión
- `POST /api/upload` - Subir imagen para procesamiento
- `POST /api/chat` - Enviar mensaje de texto
- `GET /api/stream` - Recibir respuestas en streaming
- `GET /api/health` - Verificar estado del servicio

Consulta la documentación completa en http://localhost:8000/docs cuando el servidor esté en ejecución.
