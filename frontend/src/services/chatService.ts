import axios from 'axios'

// Configuración base de Axios
const apiClient = axios.create({
  baseURL: '/api',  // Esto se redirigirá a través del proxy en desarrollo
  headers: {
    'Content-Type': 'application/json'
  }
})

// Almacena el ID de sesión actual
let sessionId: string | null = null

export const chatService = {
  /**
   * Crear una nueva sesión de chat
   */
  async createSession(): Promise<string> {
    try {
      const response = await apiClient.post('/sessions')
      sessionId = response.data.session_id
      return sessionId
    } catch (error) {
      console.error('Error al crear sesión:', error)
      throw new Error('No se pudo crear una sesión de chat')
    }
  },

  /**
   * Obtener el historial de mensajes de la sesión actual
   */
  async getHistory() {
    if (!sessionId) {
      throw new Error('No hay sesión activa')
    }

    try {
      const response = await apiClient.get(`/sessions/${sessionId}`)
      return response.data.history
    } catch (error) {
      console.error('Error al obtener historial:', error)
      throw new Error('No se pudo obtener el historial de chat')
    }
  },

  /**
   * Subir un archivo para procesamiento multimodal
   */
  async uploadFile(file: File) {
    if (!sessionId) {
      throw new Error('No hay sesión activa')
    }

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await apiClient.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-Session-ID': sessionId
        }
      })
      return response.data
    } catch (error) {
      console.error('Error al subir archivo:', error)
      throw new Error('No se pudo subir el archivo')
    }
  },

  /**
   * Enviar un mensaje de texto
   */
  async sendMessage(message: string) {
    if (!sessionId) {
      throw new Error('No hay sesión activa')
    }

    try {
      await apiClient.post('/chat', { message }, {
        headers: {
          'X-Session-ID': sessionId
        }
      })
    } catch (error) {
      console.error('Error al enviar mensaje:', error)
      throw new Error('No se pudo enviar el mensaje')
    }
  },

  /**
   * Obtener respuesta en streaming
   */
  streamResponse(): EventSource {
    if (!sessionId) {
      throw new Error('No hay sesión activa')
    }

    return new EventSource(`/api/stream?session_id=${sessionId}`, {
      withCredentials: true
    })
  }
}
