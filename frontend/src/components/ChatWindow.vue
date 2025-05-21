<template>
  <div class="flex flex-col h-[600px]">
    <!-- Chat messages area -->
    <div ref="messagesContainer" class="flex-1 overflow-auto p-4">
      <div v-if="loading" class="text-center py-4">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p class="mt-2 text-gray-500">Iniciando sesión...</p>
      </div>
      
      <div v-else-if="messages.length === 0" class="flex flex-col items-center justify-center h-full">
        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"
          class="text-gray-400 mb-4">
          <circle cx="12" cy="12" r="10" />
          <path d="M8 12h.01" />
          <path d="M12 12h.01" />
          <path d="M16 12h.01" />
        </svg>
        <p class="text-gray-500">Comienza a chatear con Gemini AI</p>
      </div>
      
      <div v-else class="space-y-4">
        <div v-for="(msg, index) in messages" :key="index" class="flex">
          <div :class="[
            'message-container',
            msg.role === 'user' ? 'user-message' : 'model-message'
          ]">
            <div class="font-semibold mb-1">{{ msg.role === 'user' ? 'Tú' : 'Gemini' }}</div>
            <div v-html="formatMessage(msg.content)"></div>
          </div>
        </div>
        
        <div v-if="isStreaming" class="flex">
          <div class="message-container model-message">
            <div class="font-semibold mb-1">Gemini</div>
            <div v-html="formatMessage(currentResponse)"></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- File upload area -->
    <div v-if="isFileUploaded" class="px-4 py-2 bg-blue-50 border-t border-blue-100">
      <div class="flex items-center">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
          class="text-blue-500 mr-2">
          <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
          <polyline points="14 2 14 8 20 8" />
        </svg>
        <span class="text-sm text-blue-600">{{ uploadedFilename }}</span>
        <button @click="removeUploadedFile" class="ml-auto text-red-500 hover:text-red-700">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    </div>
    
    <!-- Input area -->
    <div class="border-t border-gray-200 p-4">
      <div class="flex items-end">
        <div class="relative flex-grow">
          <textarea 
            v-model="userMessage" 
            @keydown.enter.prevent="sendMessage"
            placeholder="Escribe un mensaje..." 
            class="w-full border border-gray-300 rounded-lg px-4 py-2 pr-12 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows="1"
            :disabled="isStreaming || loading"
          ></textarea>
          
          <label for="file-upload" class="absolute right-2 bottom-2 cursor-pointer text-gray-500 hover:text-blue-500">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <input 
              id="file-upload" 
              type="file" 
              class="hidden" 
              accept="image/png,image/jpeg,image/jpg"
              @change="handleFileUpload"
              :disabled="isStreaming || loading"
            >
          </label>
        </div>
        
        <button 
          @click="sendMessage" 
          class="ml-2 bg-blue-600 text-white rounded-lg p-2 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          :disabled="!userMessage.trim() || isStreaming || loading"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { chatService } from '../services/chatService'

// Estado de la interfaz
const loading = ref(true)
const userMessage = ref('')
const messages = ref<{ role: string; content: string }[]>([])
const currentResponse = ref('')
const isStreaming = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)

// Estado para la carga de archivos
const isFileUploaded = ref(false)
const uploadedFile = ref<File | null>(null)
const uploadedFilename = ref('')

// Iniciar una nueva sesión al cargar el componente
onMounted(async () => {
  try {
    await chatService.createSession()
    loading.value = false
  } catch (error) {
    console.error('Error al iniciar sesión:', error)
    alert('No se pudo conectar con el servidor. Por favor, inténtalo de nuevo.')
  }
})

// Manejar la carga de archivos
const handleFileUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return
  
  const file = input.files[0]
  if (!file) return
  
  try {
    // Solo permitir imágenes
    if (!file.type.match('image.*')) {
      alert('Por favor, selecciona un archivo de imagen (JPG, JPEG o PNG)')
      return
    }
    
    await chatService.uploadFile(file)
    uploadedFile.value = file
    uploadedFilename.value = file.name
    isFileUploaded.value = true
  } catch (error) {
    console.error('Error al subir el archivo:', error)
    alert('Error al subir el archivo. Por favor, inténtalo de nuevo.')
  }
}

// Eliminar el archivo cargado
const removeUploadedFile = () => {
  uploadedFile.value = null
  uploadedFilename.value = ''
  isFileUploaded.value = false
}

// Enviar mensaje
const sendMessage = async () => {
  if (!userMessage.value.trim() || isStreaming.value || loading.value) return
  
  const messageText = userMessage.value
  userMessage.value = ''
  
  // Añadir mensaje del usuario al chat
  messages.value.push({ role: 'user', content: messageText })
  
  // Desplazar al fondo
  await nextTick()
  scrollToBottom()
  
  try {
    // Enviar mensaje al servidor
    await chatService.sendMessage(messageText)
    
    // Iniciar streaming de la respuesta
    isStreaming.value = true
    currentResponse.value = ''
    
    // Escuchar la respuesta en streaming
    const eventSource = chatService.streamResponse()
    
    eventSource.onmessage = (event) => {
      currentResponse.value += event.data
      scrollToBottom()
    }
    
    eventSource.onerror = () => {
      eventSource.close()
      isStreaming.value = false
      
      // Añadir respuesta completa al historial
      if (currentResponse.value) {
        messages.value.push({ role: 'model', content: currentResponse.value })
        currentResponse.value = ''
      } else {
        messages.value.push({
          role: 'model',
          content: 'Lo siento, hubo un error al procesar tu mensaje. Por favor, inténtalo de nuevo.'
        })
      }
      
      scrollToBottom()
      
      // Eliminar el archivo si hay alguno
      if (isFileUploaded.value) {
        removeUploadedFile()
      }
    }
  } catch (error) {
    console.error('Error al enviar mensaje:', error)
    messages.value.push({
      role: 'model',
      content: 'Lo siento, hubo un error al enviar tu mensaje. Por favor, inténtalo de nuevo.'
    })
    isStreaming.value = false
    
    if (isFileUploaded.value) {
      removeUploadedFile()
    }
  }
}

// Formatear el mensaje (conservar saltos de línea)
const formatMessage = (content: string) => {
  if (!content) return ''
  
  // Convertir URLs en enlaces
  const withLinks = content.replace(
    /(https?:\/\/[^\s]+)/g,
    '<a href="$1" target="_blank" class="text-blue-600 hover:underline">$1</a>'
  )
  
  // Conservar saltos de línea
  return withLinks.replace(/\n/g, '<br>')
}

// Desplazar al fondo del contenedor de mensajes
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}
</script>
