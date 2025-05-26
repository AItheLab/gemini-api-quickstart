import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

let currentSessionId: string | null = null

// Interfaces para tipado
interface ChatMetadata {
  session_id: string
  title: string
  created_at: number
  updated_at: number
  message_count: number
  last_message_preview: string
  tags: string[]
  is_pinned: boolean
}

interface ChatListResponse {
  success: boolean
  chats: ChatMetadata[]
  total: number
}

export const chatService = {
  // Método para inicializar el servicio
  initialize(): void {
    console.log('chatService: Initialized')
  },

  async createSession(): Promise<string> {
    try {
      const response = await apiClient.post('/sessions')
      const newSessionId = response.data.session_id
      if (newSessionId) {
        currentSessionId = newSessionId
        console.log('Nueva sesión creada con ID:', newSessionId)
      } else {
        throw new Error('El servidor no devolvió un ID de sesión válido')
      }
      return newSessionId
    } catch (error) {
      console.error('Error al crear sesión:', error)
      throw new Error('No se pudo crear una sesión de chat')
    }
  },

  setActiveSession(sessionId: string | null) {
    currentSessionId = sessionId
  },

  getActiveSession(): string | null {
    return currentSessionId
  },

  // NUEVO: Obtener todos los chats desde el backend
  async getAllChats(): Promise<ChatMetadata[]> {
    try {
      const response = await apiClient.get<ChatListResponse>('/chats')
      if (response.data.success) {
        return response.data.chats
      } else {
        throw new Error('Error en la respuesta del servidor')
      }
    } catch (error) {
      console.error('Error al obtener lista de chats:', error)
      return [] // Retornar array vacío en caso de error
    }
  },

  // NUEVO: Buscar chats
  async searchChats(query: string): Promise<ChatMetadata[]> {
    try {
      const response = await apiClient.get<ChatListResponse>(`/chats?search=${encodeURIComponent(query)}`)
      if (response.data.success) {
        return response.data.chats
      } else {
        throw new Error('Error en la búsqueda')
      }
    } catch (error) {
      console.error('Error al buscar chats:', error)
      return []
    }
  },

  // NUEVO: Eliminar chat usando la API del backend
  async removeSession(sessionId: string): Promise<boolean> {
    try {
      const response = await apiClient.delete(`/chats/${sessionId}`)
      if (response.data.success) {
        // Si eliminamos la sesión activa, limpiar la referencia
        if (currentSessionId === sessionId) {
          currentSessionId = null
        }
        console.log(`Chat ${sessionId} eliminado correctamente`)
        return true
      } else {
        throw new Error(response.data.message || 'Error al eliminar chat')
      }
    } catch (error) {
      console.error('Error al eliminar chat:', error)
      return false
    }
  },

  // NUEVO: Actualizar metadatos del chat
  async updateChatMetadata(sessionId: string, updates: {
    title?: string
    add_tags?: string[]
    remove_tags?: string[]
    toggle_pin?: boolean
  }): Promise<boolean> {
    try {
      const response = await apiClient.put(`/chats/${sessionId}`, updates)
      if (response.data.success) {
        console.log(`Metadatos del chat ${sessionId} actualizados`)
        return true
      } else {
        throw new Error(response.data.message || 'Error al actualizar metadatos')
      }
    } catch (error) {
      console.error('Error al actualizar metadatos:', error)
      return false
    }
  },

  async getHistory(sessionId: string) {
    if (!sessionId) {
      throw new Error('Session ID requerido')
    }

    try {
      const response = await apiClient.get(`/sessions/${sessionId}`)
      return response.data.history
    } catch (error) {
      console.error(`Error al obtener historial para sesión ${sessionId}:`, error)
      if (axios.isAxiosError(error) && error.response && error.response.status === 404) {
        console.warn(`Sesión ${sessionId} no encontrada en el backend.`)
      }
      throw new Error(`No se pudo obtener el historial de chat para la sesión ${sessionId}`)
    }
  },

  async uploadFile(file: File, sessionId: string) {
    if (!sessionId) throw new Error('No hay sesión activa para subir archivo')

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

  async sendMessage(message: string, sessionId: string) {
    if (!sessionId) throw new Error('No hay sesión activa para enviar mensaje')

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

  streamResponse(sessionId: string): EventSource {
    if (!sessionId) throw new Error('No hay sesión activa para stream')

    const url = `/api/stream?session_id=${sessionId}`
    return new EventSource(url, { withCredentials: true })
  }
}
