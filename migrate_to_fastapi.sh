#!/bin/bash

# Dar permisos de ejecución al script
chmod +x setup_frontend.sh

# Eliminar archivos de Flask que ya no se necesitan
echo "Eliminando archivos relacionados con Flask..."
rm -rf app.py
rm -rf templates
rm -rf static

echo "Añadir .gitignore si no existe"
if [ ! -f .gitignore ]; then
  cat > .gitignore << EOL
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/
.env

# Node.js
node_modules/
dist/
dist-ssr/
*.local

# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

# Uploads
uploads/
EOL
fi

echo "Migración completada."
echo "Para iniciar el backend, ejecute: uvicorn main:app --reload"
echo "Para configurar el frontend, ejecute: ./setup_frontend.sh"
