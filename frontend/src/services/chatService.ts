import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

const SESSION_IDS_KEY = 'geminiChatSessionIds'
let currentSessionId: string | null = null; // Almacenar el ID de la sesión activa en memoria

// Cargar el último session ID activo o el primero de la lista al iniciar
const loadInitialSessionId = (): string | null => {
    const ids = getSessionIdsFromStorage();
    // Podrías añadir lógica para recordar el último activo aquí si lo guardas también
    return ids.length > 0 ? ids[0] : null;
};

// No inicializar currentSessionId durante la importación del módulo
// currentSessionId = loadInitialSessionId(); 


const getSessionIdsFromStorage = (): string[] => {
  const storedIds = localStorage.getItem(SESSION_IDS_KEY)
  return storedIds ? JSON.parse(storedIds) : []
}

const saveSessionIdToStorage = (sessionId: string) => {
  const ids = getSessionIdsFromStorage()
  if (!ids.includes(sessionId)) {
    ids.unshift(sessionId) // Añadir al principio para que el más nuevo esté arriba
    localStorage.setItem(SESSION_IDS_KEY, JSON.stringify(ids))
  }
}

const removeSessionIdFromStorage = (sessionIdToRemove: string) => {
    let ids = getSessionIdsFromStorage();
    ids = ids.filter(id => id !== sessionIdToRemove);
    localStorage.setItem(SESSION_IDS_KEY, JSON.stringify(ids));
    if (currentSessionId === sessionIdToRemove) {
        currentSessionId = ids.length > 0 ? ids[0] : null; // Cambia a la siguiente o a null
    }
};


export const chatService = {
  // Método para inicializar el servicio de forma explícita
  initialize(): void {
    if (currentSessionId === null) {
      currentSessionId = loadInitialSessionId();
      console.log('chatService: Initialized with session ID:', currentSessionId);
    }
  },

  async createSession(): Promise<string> {
    try {
      // Usar el nuevo endpoint /sessions implementado en el backend
      const response = await apiClient.post('/sessions')
      const newSessionId = response.data.session_id
      if (newSessionId) {
        saveSessionIdToStorage(newSessionId)
        currentSessionId = newSessionId; // Establecer como la sesión activa
        console.log('Nueva sesión creada con ID:', newSessionId);
      } else {
        throw new Error('El servidor no devolvió un ID de sesión válido');
      }
      return newSessionId
    } catch (error) {
      console.error('Error al crear sesión:', error)
      throw new Error('No se pudo crear una sesión de chat')
    }
  },

  setActiveSession(sessionId: string | null) {
    currentSessionId = sessionId;
    // Opcional: guardar el último sessionId activo en localStorage también
  },

  getActiveSession(): string | null {
    if (!currentSessionId) { // Si no hay uno activo, intenta cargar el primero de la lista
        const ids = getSessionIdsFromStorage();
        if (ids.length > 0) {
            currentSessionId = ids[0];
        }
    }
    return currentSessionId;
  },

  getAllSessionIds(): string[] {
    return getSessionIdsFromStorage()
  },

  removeSession(sessionIdToRemove: string): void {
    removeSessionIdFromStorage(sessionIdToRemove);
  },

  async getHistory(sessionId: string) { // Ahora requiere sessionId
    if (!sessionId) {
      // Intenta obtener la activa si no se provee una específica, aunque es mejor ser explícito
      const activeId = this.getActiveSession();
      if (!activeId) throw new Error('No hay sesión activa o ID de sesión provisto');
      sessionId = activeId;
    }

    try {
      const response = await apiClient.get(`/sessions/${sessionId}`)
      return response.data.history
    } catch (error) {
      console.error(`Error al obtener historial para sesión ${sessionId}:`, error)
      // Podrías querer limpiar una sesión inválida del storage aquí
      if (axios.isAxiosError(error) && error.response && error.response.status === 404) {
        console.warn(`Sesión ${sessionId} no encontrada en el backend. Removiendo del historial local.`);
        removeSessionIdFromStorage(sessionId); // Limpia sesión inválida
        // Podrías emitir un evento o manejar el cambio de UI aquí
      }
      throw new Error(`No se pudo obtener el historial de chat para la sesión ${sessionId}`)
    }
  },

  async uploadFile(file: File, sessionId: string) { // Requiere sessionId
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

  async sendMessage(message: string, sessionId: string) { // Requiere sessionId
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

  streamResponse(sessionId: string): EventSource { // Requiere sessionId
    if (!sessionId) throw new Error('No hay sesión activa para stream')

    const url = `/api/stream?session_id=${sessionId}`
    // EventSource no permite cabeceras personalizadas fácilmente para GET,
    // el backend ya acepta session_id como query param, lo cual es bueno.
    return new EventSource(url, { withCredentials: true })
  }
}
