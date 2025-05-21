#!/bin/bash

# Este script configura un nuevo proyecto frontend usando Vue 3, Vite, TypeScript, y Tailwind CSS

# Verificar si npm está instalado
if ! command -v npm &> /dev/null; then
    echo "Error: npm no está instalado. Por favor instala Node.js y npm primero."
    exit 1
fi

# Verificar si yarn está instalado, de lo contrario usar npm
if command -v yarn &> /dev/null; then
    PACKAGE_MANAGER=yarn
else
    PACKAGE_MANAGER=npm
fi

echo "Usando $PACKAGE_MANAGER para la instalación de paquetes"

# Navegar a la carpeta frontend
cd "$(dirname "$0")/frontend" || exit 1

# Inicializar proyecto Vue 3 + Vite + TypeScript
echo "Creando un nuevo proyecto Vue 3 + Vite + TypeScript..."
if [ "$PACKAGE_MANAGER" = "yarn" ]; then
    yarn create vite . --template vue-ts
else
    npm create vite@latest . -- --template vue-ts
fi

# Instalar dependencias
echo "Instalando dependencias..."
$PACKAGE_MANAGER install

# Agregar Tailwind CSS
echo "Configurando Tailwind CSS..."
$PACKAGE_MANAGER add -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Crear archivos de configuración para Tailwind
cat > tailwind.config.js << EOL
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
EOL

# Crear archivo CSS con directivas de Tailwind
cat > src/assets/index.css << EOL
@tailwind base;
@tailwind components;
@tailwind utilities;
EOL

# Modificar el archivo main.ts para importar el CSS
# La siguiente línea puede necesitar ajustes según el sistema operativo
# Para macOS:
if [[ "$OSTYPE" == "darwin"* ]]; then
  sed -i '' 's|import "./style.css"|import "./assets/index.css"|' src/main.ts
else
  sed -i 's|import "./style.css"|import "./assets/index.css"|' src/main.ts
fi

# Instalar Axios para las llamadas a la API
echo "Instalando Axios para llamadas a la API..."
$PACKAGE_MANAGER add axios

# Crear estructura de carpetas para el proyecto
echo "Creando estructura de carpetas..."
mkdir -p src/components/chat
mkdir -p src/services
mkdir -p src/types
mkdir -p src/views
mkdir -p src/stores

# Crear archivo de configuración para la API
cat > src/services/api.ts << EOL
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar el ID de sesión a todas las solicitudes
apiClient.interceptors.request.use((config) => {
  const sessionId = localStorage.getItem('sessionId');
  if (sessionId) {
    config.headers['X-Session-ID'] = sessionId;
  }
  return config;
});

export default apiClient;
EOL

# Crear archivo .env para la configuración
cat > .env << EOL
VITE_API_BASE_URL=http://localhost:8000/api
EOL

# Crear archivo .env.production
cat > .env.production << EOL
VITE_API_BASE_URL=/api
EOL

# Crear archivo de tipos para el chat
cat > src/types/chat.ts << EOL
export interface Message {
  role: 'user' | 'model';
  content: string;
}

export interface Session {
  id: string;
  history: Message[];
}
EOL

# Crear archivo README para el frontend
cat > README.md << EOL
# Frontend Gemini Chat (Vue 3 + Vite + TypeScript + Tailwind)

Este es el frontend para la aplicación Gemini Chat, construido con Vue 3, Vite, TypeScript y Tailwind CSS.

## Configuración del proyecto

\`\`\`bash
# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev

# Compilar para producción
npm run build
\`\`\`

## Variables de entorno

- \`VITE_API_BASE_URL\`: URL base para la API del backend (por defecto: http://localhost:8000/api)

## Estructura del proyecto

\`\`\`
src/
├── assets/             # Archivos estáticos (CSS, imágenes)
├── components/         # Componentes Vue reutilizables
│   └── chat/           # Componentes específicos del chat
├── services/           # Servicios para comunicación con APIs
├── stores/             # Estado global (Pinia)
├── types/              # Definiciones de tipos TypeScript
└── views/              # Componentes de página/vista
\`\`\`
EOL

echo "¡Configuración del frontend completada!"
echo "Para iniciar el servidor de desarrollo, ejecuta:"
echo "cd frontend && $PACKAGE_MANAGER run dev"
