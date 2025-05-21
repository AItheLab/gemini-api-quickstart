/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'ch-bg-darkest': '#17181A', // Fondo general más oscuro
        'ch-bg-panel': '#1E1F22',   // Paneles ligeramente más claros (sidebar, cabecera)
        'ch-bg-chat-area': '#232528', // Fondo del área de conversación
        'ch-bg-input': '#1D1E20',   // Fondo de la barra de entrada de mensajes
        'ch-bubble-user': '#377DFF', // Azul vibrante para burbujas del usuario
        'ch-bubble-user-text': '#FFFFFF',
        'ch-bubble-other': '#36373A', // Gris oscuro para burbujas de otros
        'ch-bubble-other-text': '#E0E0E0',
        'ch-text-primary': '#EAEAEA', // Texto principal (muy claro)
        'ch-text-secondary': '#A0A2A5', // Texto secundario (gris medio)
        'ch-text-placeholder': '#6C6D70', // Para placeholders
        'ch-icon': '#AEAEB2',         // Iconos
        'ch-border': '#3A3B3D',        // Bordes sutiles y divisores
        'ch-accent': '#377DFF',        // Acento principal (puede ser el mismo que bubble-user)
        'ch-destructive': '#FF3B30',   // Para acciones destructivas (ej. borrar)
        'ch-unread-badge': '#377DFF',   // Notificaciones/Badges
      }
    },
  },
  plugins: [],
}