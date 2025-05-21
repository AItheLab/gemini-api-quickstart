<template>
  <div class="flex flex-col h-full"> <!-- Changed h-[600px] to h-full -->
    <!-- Chat messages area -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 bg-gray-50"> <!-- Adjusted padding for responsiveness -->
      <div v-if="loading" class="flex flex-col items-center justify-center h-full text-gray-500">
        <div class="inline-block animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-600 mb-3"></div>
        <p>Iniciando sesión...</p>
      </div>
      
      <div v-else-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-gray-500">
        <svg xmlns="http://www.w3.org/2000/svg" width="72" height="72" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"
          class="text-gray-400 mb-4">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 16c-3.31 0-6-2.69-6-6s2.69-6 6-6 6 2.69 6 6-2.69 6-6 6zm-1-5h2v2h-2zm0-4h2v2h-2z"/>
        </svg>
        <p class="text-lg">Comienza a chatear con Gemini AI</p>
      </div>
      
      <div v-else>
        <div v-for="(msg, index) in messages" :key="index" 
             :class="[
               'flex', 
               msg.role === 'user' ? 'justify-end' : 'justify-start'
             ]">
          <div :class="[
            'p-3 rounded-xl shadow-md max-w-lg break-words',
            msg.role === 'user' 
              ? 'bg-blue-500 text-white' 
              : 'bg-white text-gray-800 border border-gray-200'
          ]">
            <div class="font-bold text-sm mb-1">{{ msg.role === 'user' ? 'Tú' : 'Gemini' }}</div>
            <div v-html="formatMessage(msg.content)" class="text-sm leading-relaxed"></div>
          </div>
        </div>
        
        <div v-if="isStreaming" class="flex justify-start">
          <div class="p-3 rounded-xl shadow-md max-w-lg break-words bg-white text-gray-800 border border-gray-200">
            <div class="font-bold text-sm mb-1">Gemini</div>
            <div v-html="formatMessage(currentResponse)" class="text-sm leading-relaxed"></div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- File upload preview area -->
    <div v-if="isFileUploaded" class="px-4 py-3 bg-blue-50 border-t border-b border-blue-200">
      <div class="flex items-center justify-between">
        <div class="flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
            class="text-blue-600 mr-3">
            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          <span class="text-sm text-blue-700 font-medium">{{ uploadedFilename }}</span>
        </div>
        <button @click="removeUploadedFile" class="text-red-500 hover:text-red-700 p-1 rounded-full hover:bg-red-100">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    </div>
    
    <!-- Input area -->
    <div class="bg-white border-t border-gray-200 p-4">
      <div class="flex items-center space-x-2 sm:space-x-3"> <!-- Adjusted spacing for responsiveness -->
        <label for="file-upload" class="cursor-pointer text-gray-500 hover:text-blue-600 p-2 rounded-full hover:bg-gray-100">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21.2 15c.7-1.2 1-2.5.7-3.9-.6-2.4-3-4.1-5.5-4.1-1.4 0-2.7.6-3.6 1.5M12 21H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h5.5" />
            <path d="M16 16L12 12 8 16" />
            <path d="M12 12V21" />
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
        <textarea 
          v-model="userMessage" 
          @keydown.enter.prevent="sendMessage"
          placeholder="Escribe tu mensaje a Gemini..." 
          class="flex-grow border border-gray-300 rounded-xl px-4 py-2.5 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-shadow duration-150"
          rows="1"
          :disabled="isStreaming || loading"
          ref="textareaRef"
          @input="adjustTextareaHeight"
        ></textarea>
        
        <button 
          @click="sendMessage" 
          class="bg-blue-600 text-white rounded-lg p-2.5 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150"
          :disabled="(!userMessage.trim() && !isFileUploaded) || isStreaming || loading"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12h14" />
            <path d="M12 5l7 7-7 7" />
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
const textareaRef = ref<HTMLTextAreaElement | null>(null)

// Estado para la carga de archivos
const isFileUploaded = ref(false)
const uploadedFile = ref<File | null>(null)
const uploadedFilename = ref('')

// Iniciar una nueva sesión al cargar el componente
onMounted(async () => {
  try {
    await chatService.createSession()
    loading.value = false
    await nextTick()
    adjustTextareaHeight()
  } catch (error) {
    console.error('Error al iniciar sesión:', error)
    alert('No se pudo conectar con el servidor. Por favor, inténtalo de nuevo.')
  }
})

// Ajustar altura del textarea
const adjustTextareaHeight = () => {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto';
    textareaRef.value.style.height = `${textareaRef.value.scrollHeight}px`;
  }
}

watch(userMessage, () => {
  adjustTextareaHeight()
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
      input.value = '' // Reset file input
      return
    }
    
    await chatService.uploadFile(file)
    uploadedFile.value = file
    uploadedFilename.value = file.name
    isFileUploaded.value = true
  } catch (error) {
    console.error('Error al subir el archivo:', error)
    alert('Error al subir el archivo. Por favor, inténtalo de nuevo.')
  } finally {
    input.value = '' // Reset file input
  }
}

// Eliminar el archivo cargado
const removeUploadedFile = () => {
  uploadedFile.value = null
  uploadedFilename.value = ''
  isFileUploaded.value = false
  // Aquí podrías llamar a un servicio para eliminar el archivo del backend si es necesario
}

// Enviar mensaje
const sendMessage = async () => {
  if ((!userMessage.value.trim() && !isFileUploaded.value) || isStreaming.value || loading.value) return
  
  const messageText = userMessage.value
  userMessage.value = '' // Clear input after preparing message
  
  // Añadir mensaje del usuario al chat
  messages.value.push({ role: 'user', content: messageText })
  
  // Desplazar al fondo y resetear altura del textarea
  await nextTick()
  scrollToBottom()
  adjustTextareaHeight() // Reset height after sending
  
  try {
    // Enviar mensaje al servidor
    await chatService.sendMessage(messageText, isFileUploaded.value ? uploadedFile.value : undefined)
    
    // Iniciar streaming de la respuesta
    isStreaming.value = true
    currentResponse.value = ''
    
    // Limpiar el archivo subido después de enviarlo con el mensaje
    if (isFileUploaded.value) {
        removeUploadedFile()
    }

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
    }
  } catch (error) {
    console.error('Error al enviar mensaje:', error)
    messages.value.push({
      role: 'model',
      content: 'Lo siento, hubo un error al enviar tu mensaje. Por favor, inténtalo de nuevo.'
    })
    isStreaming.value = false
    
    // Limpiar el archivo subido en caso de error también
    if (isFileUploaded.value) {
        removeUploadedFile()
    }
  }
}

// Formatear el mensaje (conservar saltos de línea y convertir URLs)
const formatMessage = (content: string) => {
  if (!content) return ''
  
  // Escapar HTML para prevenir XSS, excepto lo que queremos permitir (br, a)
  const escapeHtml = (unsafe: string) => {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
  }

  let safeContent = escapeHtml(content);

  // Convertir URLs en enlaces (después de escapar)
  safeContent = safeContent.replace(
    /(https?:\/\/[^\s]+)/g,
    '<a href="$1" target="_blank" rel="noopener noreferrer" class="text-blue-500 hover:underline">$1</a>'
  )
  
  // Conservar saltos de línea (reemplazar \n con <br> después de escapar)
  return safeContent.replace(/\n/g, '<br>')
}

// Desplazar al fondo del contenedor de mensajes
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// Actualizar la condición del botón de enviar
const sendButtonDisabled = computed(() => {
  return (!userMessage.value.trim() && !isFileUploaded.value) || isStreaming.value || loading.value;
});

// Watch para reajustar altura del textarea cuando el contenedor de mensajes cambie (e.g. teclado virtual en móvil)
watch(messagesContainer, () => {
  if (messagesContainer.value) {
    const resizeObserver = new ResizeObserver(() => {
      scrollToBottom();
      adjustTextareaHeight();
    });
    resizeObserver.observe(messagesContainer.value);
  }
});

</script>

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
