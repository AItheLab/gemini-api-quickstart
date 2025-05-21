<template>
  <div class="flex flex-col h-full bg-ch-bg-chat-area text-ch-text-primary">
    <!-- Chat messages area -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
      <div v-if="componentLoading" class="flex flex-col items-center justify-center h-full text-ch-text-secondary">
        <div class="inline-block animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-ch-accent mb-3"></div>
        <p>Cargando mensajes...</p>
      </div>

      <div v-else-if="messages.length === 0 && !isStreaming" class="flex flex-col items-center justify-center h-full text-ch-text-secondary">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-16 h-16 mb-4 text-ch-icon">
          <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.76c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.184-4.183a.38.38 0 01.265-.112 23.895 23.895 0 005.86-.498c1.585-.233 2.708-1.626 2.708-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
        </svg>
        <p class="text-lg">Envía un mensaje para empezar.</p>
        <p class="text-sm mt-1">O adjunta una imagen.</p>
      </div>

      <div v-else class="space-y-6">
        <div v-for="(msg, index) in messages" :key="`${props.sessionId}-${index}`" class="flex items-end space-x-2 mb-2"
             :class="[msg.role === 'user' ? 'justify-end' : 'justify-start']">
          <div v-if="msg.role === 'model'" class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex-shrink-0 flex items-center justify-center text-xs text-white mb-1 shadow-md">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-cpu">
              <rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect>
              <rect x="9" y="9" width="6" height="6"></rect>
              <line x1="9" y1="1" x2="9" y2="4"></line>
              <line x1="15" y1="1" x2="15" y2="4"></line>
              <line x1="9" y1="20" x2="9" y2="23"></line>
              <line x1="15" y1="20" x2="15" y2="23"></line>
              <line x1="20" y1="9" x2="23" y2="9"></line>
              <line x1="20" y1="14" x2="23" y2="14"></line>
              <line x1="1" y1="9" x2="4" y2="9"></line>
              <line x1="1" y1="14" x2="4" y2="14"></line>
            </svg>
          </div>
          <div :class="[
            'px-4 py-3 rounded-2xl shadow-lg max-w-xl break-words transition-all duration-200',
            msg.role === 'user'
              ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-br-none transform hover:scale-[101%]'
              : 'bg-gradient-to-r from-gray-700 to-gray-800 text-white rounded-bl-none transform hover:scale-[101%]'
          ]">
            <div v-html="formatMessage(msg.content)" class="text-sm md:text-base leading-relaxed"></div>
            <div class="text-xs mt-2 opacity-70" :class="msg.role === 'user' ? 'text-right' : 'text-left'">
              {{ new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}
            </div>
          </div>
          <div v-if="msg.role === 'user'" class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex-shrink-0 flex items-center justify-center text-xs text-white mb-1 shadow-md">
            TÚ
          </div>
        </div>
        <div v-if="isStreaming" class="flex items-end space-x-2 justify-start">
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex-shrink-0 flex items-center justify-center text-xs text-white mb-1 shadow-md">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-cpu">
              <rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect>
              <rect x="9" y="9" width="6" height="6"></rect>
              <line x1="9" y1="1" x2="9" y2="4"></line>
              <line x1="15" y1="1" x2="15" y2="4"></line>
              <line x1="9" y1="20" x2="9" y2="23"></line>
              <line x1="15" y1="20" x2="15" y2="23"></line>
              <line x1="20" y1="9" x2="23" y2="9"></line>
              <line x1="20" y1="14" x2="23" y2="14"></line>
              <line x1="1" y1="9" x2="4" y2="9"></line>
              <line x1="1" y1="14" x2="4" y2="14"></line>
            </svg>
          </div>
          <div class="px-4 py-3 rounded-2xl shadow-lg max-w-xl break-words bg-gradient-to-r from-gray-700 to-gray-800 text-white rounded-bl-none animate-fade-in">
            <div v-html="formatMessage(currentResponse)" class="text-sm md:text-base leading-relaxed"></div>
            <div class="flex mt-2 space-x-1 justify-start">
              <div class="animate-bounce-delay-1 w-2 h-2 bg-blue-400 rounded-full"></div>
              <div class="animate-bounce-delay-2 w-2 h-2 bg-blue-400 rounded-full"></div>
              <div class="animate-bounce-delay-3 w-2 h-2 bg-blue-400 rounded-full"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="isFileUploaded" class="px-4 py-2.5 bg-ch-bg-input border-t border-ch-border">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-ch-accent">
            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" /><polyline points="14 2 14 8 20 8" />
          </svg>
          <span class="text-sm text-ch-text-secondary font-medium">{{ uploadedFilename }}</span>
        </div>
        <button @click="removeUploadedFile" class="text-ch-icon hover:text-ch-destructive p-1 rounded-full hover:bg-ch-destructive/10">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
        </button>
      </div>
    </div>

    <div class="bg-ch-bg-input border-t border-ch-border p-3">
      <div class="flex items-end space-x-2 sm:space-x-3">
        <label for="file-upload" title="Adjuntar imagen" class="cursor-pointer text-ch-icon hover:text-ch-accent p-2.5 rounded-lg hover:bg-ch-bg-panel flex-shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>
          <input id="file-upload" type="file" class="hidden" accept="image/png,image/jpeg,image/jpg" @change="handleFileUpload" :disabled="isStreaming || componentLoading" >
        </label>
        <textarea
          v-model="userMessage"
          @keydown.enter.exact.prevent="sendMessage"
          placeholder="Escribe tu mensaje..."
          class="flex-grow bg-ch-bg-panel border border-transparent text-ch-text-primary rounded-lg px-4 py-2.5 resize-none focus:outline-none focus:ring-2 focus:ring-ch-accent focus:border-ch-accent transition-shadow duration-150 min-h-[44px]"
          rows="1"
          :disabled="isStreaming || componentLoading"
          ref="textareaRef"
          @input="adjustTextareaHeight"
        ></textarea>
        <button
          @click="sendMessage"
          title="Enviar mensaje"
          class="bg-ch-accent text-white rounded-lg p-2.5 hover:bg-opacity-80 focus:outline-none focus:ring-2 focus:ring-ch-accent/50 focus:ring-offset-1 focus:ring-offset-ch-bg-input disabled:opacity-60 disabled:cursor-not-allowed transition-colors duration-150 flex-shrink-0"
          :disabled="sendButtonDisabled"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transform rotate-45 -mr-px -mt-px">
            <line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick, defineProps, onBeforeUnmount } from 'vue'
import { chatService } from '../services/chatService'

const props = defineProps<{
  sessionId: string
}>()

console.log(`ChatWindow (${props.sessionId || 'NO SESSION ID YET'}): script setup evaluated`);

const componentLoading = ref(true)
const userMessage = ref('')
const messages = ref<{ role: string; content: string }[]>([])
const currentResponse = ref('')
const isStreaming = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const isFileUploaded = ref(false)
const uploadedFile = ref<File | null>(null)
const uploadedFilename = ref('')

let observer: ResizeObserver | null = null;
let activeEventSource: EventSource | null = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 3;
const RECONNECT_DELAY = 2000; // 2 segundos

// Función para cerrar el EventSource activo si existe
const closeEventSourceIfExists = () => {
  if (activeEventSource) {
    console.log(`ChatWindow (${props.sessionId}): Closing existing EventSource.`);
    activeEventSource.close();
    activeEventSource = null;
    reconnectAttempts = 0; // Resetear intentos de reconexión al cerrar manualmente
  }
};

// Función para crear un EventSource con reconexión automática
const createEventSourceWithRetry = (sessionId: string): EventSource => {
  console.log(`ChatWindow (${sessionId}): Creating EventSource (attempt ${reconnectAttempts + 1}/${MAX_RECONNECT_ATTEMPTS + 1})`);
  
  const eventSource = chatService.streamResponse(sessionId);
  
  eventSource.onopen = () => {
    console.log(`ChatWindow (${sessionId}): EventSource connection opened successfully.`);
    reconnectAttempts = 0; // Resetear intentos al conectar exitosamente
  };
  
  return eventSource;
};

const loadChatHistory = async (sessionIdToLoad: string) => {
  if (!sessionIdToLoad) {
    console.warn(`ChatWindow: loadChatHistory Aborted - sessionIdToLoad is null/empty.`);
    componentLoading.value = false; // Ensure loading state is reset
    return;
  }
  console.log(`ChatWindow (${sessionIdToLoad}): loadChatHistory Initiated.`);
  componentLoading.value = true;
  messages.value = [];
  try {
    const history = await chatService.getHistory(sessionIdToLoad);
    messages.value = history;
    console.log(`ChatWindow (${sessionIdToLoad}): History loaded successfully.`, messages.value.length, "messages");
  } catch (error) {
    console.error(`ChatWindow (${sessionIdToLoad}): Error loading history:`, error);
    messages.value.push({role: 'model', content: `Error al cargar el historial del chat: ${ (error as Error).message}`})
  } finally {
    componentLoading.value = false;
    await nextTick();
    scrollToBottom();
    console.log(`ChatWindow (${sessionIdToLoad}): loadChatHistory Finished.`);
  }
};

onMounted(async () => {
  console.log(`ChatWindow (${props.sessionId || 'NO SESSION ID ON MOUNT'}): onMounted triggered.`);
  if (props.sessionId) {
    await loadChatHistory(props.sessionId);
  } else {
    console.warn(`ChatWindow: onMounted - props.sessionId is not available. History will not be loaded yet.`);
    componentLoading.value = false; 
  }
  adjustTextareaHeight();

  if (messagesContainer.value) {
    observer = new ResizeObserver(() => {
      scrollToBottom();
    });
    observer.observe(messagesContainer.value);
    console.log(`ChatWindow (${props.sessionId || 'NO SESSION ID ON MOUNT'}): ResizeObserver attached.`);
  } else {
    console.warn(`ChatWindow (${props.sessionId || 'NO SESSION ID ON MOUNT'}): messagesContainer ref not available for ResizeObserver.`);
  }
});

onBeforeUnmount(() => {
  // Limpiar ResizeObserver
  if (observer && messagesContainer.value) {
    observer.unobserve(messagesContainer.value);
    console.log(`ChatWindow (${props.sessionId || 'NO SESSION ID ON UNMOUNT'}): ResizeObserver unobserved.`);
  }
  if (observer) {
    observer.disconnect();
    console.log(`ChatWindow (${props.sessionId || 'NO SESSION ID ON UNMOUNT'}): ResizeObserver disconnected.`);
  }
  
  // Limpiar EventSource para evitar fugas de memoria y conexiones colgantes
  closeEventSourceIfExists();
  
  console.log(`ChatWindow (${props.sessionId || 'NO SESSION ID ON UNMOUNT'}): onBeforeUnmount triggered.`);
});

watch(() => props.sessionId, async (newSessionId, oldSessionId) => {
  console.log(`ChatWindow: props.sessionId watcher. New: ${newSessionId}, Old: ${oldSessionId}`);
  if (newSessionId && newSessionId !== oldSessionId) {
    console.log(`ChatWindow (${newSessionId}): Session ID changed, loading history.`);
    await loadChatHistory(newSessionId);
  } else if (newSessionId && !oldSessionId) {
    // This case handles if sessionId was initially null/undefined and then set.
    // onMounted should ideally handle the very first load if sessionId is present at that time.
    console.log(`ChatWindow (${newSessionId}): Session ID initialized via watcher, loading history.`);
    await loadChatHistory(newSessionId);
  } else if (!newSessionId) {
    console.log(`ChatWindow: Session ID became null/undefined. Clearing messages.`);
    messages.value = [];
    componentLoading.value = false; // No session, so not loading.
  }
}, { immediate: false }); // immediate: false is generally safer unless explicitly needed.

const adjustTextareaHeight = () => {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto';
    const maxHeight = 120;
    const scrollHeight = textareaRef.value.scrollHeight;
    textareaRef.value.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
    textareaRef.value.style.overflowY = scrollHeight > maxHeight ? 'auto' : 'hidden';
  }
}

watch(userMessage, adjustTextareaHeight);

const handleFileUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (!input.files || input.files.length === 0) return;
  const file = input.files[0];
  if (!file) return;
  if (!file.type.match('image.*')) {
    alert('Por favor, selecciona un archivo de imagen (JPG, JPEG o PNG)');
    input.value = ''; return;
  }
  uploadedFile.value = file;
  uploadedFilename.value = file.name;
  isFileUploaded.value = true;
  input.value = ''; 
};

const removeUploadedFile = () => {
  uploadedFile.value = null;
  uploadedFilename.value = '';
  isFileUploaded.value = false;
};

const sendMessage = async () => {
  if ((!userMessage.value.trim() && !isFileUploaded.value) || isStreaming.value || componentLoading.value || !props.sessionId) {
    console.warn("ChatWindow: Send message aborted. Conditions not met.", {
        noTextOrFile: (!userMessage.value.trim() && !isFileUploaded.value),
        isStreaming: isStreaming.value,
        componentLoading: componentLoading.value,
        noSessionId: !props.sessionId
    });
    return;
  }
  
  console.log(`ChatWindow (${props.sessionId}): Sending message...`);
  const messageText = userMessage.value.trim();
  const currentFileToUpload = uploadedFile.value;

  if (messageText || currentFileToUpload) {
    messages.value.push({ role: 'user', content: messageText || `Archivo: ${currentFileToUpload?.name}` });
  }
  
  userMessage.value = '';
  if (isFileUploaded.value) removeUploadedFile();
  
  await nextTick();
  scrollToBottom();
  adjustTextareaHeight();

  isStreaming.value = true;
  currentResponse.value = '';

  try {
    // Cerrar cualquier EventSource existente antes de crear uno nuevo
    closeEventSourceIfExists();
    
    if (currentFileToUpload) {
      console.log(`ChatWindow (${props.sessionId}): Uploading file: ${currentFileToUpload.name}`);
      await chatService.uploadFile(currentFileToUpload, props.sessionId);
    }
    console.log(`ChatWindow (${props.sessionId}): Sending text message to service.`);
    await chatService.sendMessage(messageText, props.sessionId);

    // Crear y almacenar la nueva instancia de EventSource con reintentos
    reconnectAttempts = 0; // Reiniciar contador de intentos
    activeEventSource = createEventSourceWithRetry(props.sessionId);
    
    // Configurar el manejador de mensajes
    activeEventSource.onmessage = (event) => {
      if (event.data === '[DONE]') {
        console.log(`ChatWindow (${props.sessionId}): Stream finished.`);
        isStreaming.value = false;
        if (currentResponse.value) {
          messages.value.push({ role: 'model', content: currentResponse.value });
          currentResponse.value = '';
        }
        closeEventSourceIfExists(); // Close the connection after receiving DONE
      } else if (event.data.startsWith("[Error:")) {
        console.error(`ChatWindow (${props.sessionId}): Stream error received: ${event.data}`);
        currentResponse.value += event.data; // Append error to show in UI
        closeEventSourceIfExists();
        isStreaming.value = false;
        if (currentResponse.value) {
          messages.value.push({ role: 'model', content: currentResponse.value });
          currentResponse.value = '';
        }
      } else {
        currentResponse.value += event.data;
      }
      scrollToBottom();
    };
    
    // Configurar el manejador de errores con reintentos
    activeEventSource.onerror = (error) => {
      console.error(`ChatWindow (${props.sessionId}): EventSource error:`, error);
      
      // Solo procesar si estamos realmente en estado de streaming
      // Check if the error is a natural closure after DONE has been processed
      if (isStreaming.value) {
        // Cerrar la conexión actual
        if (activeEventSource) {
          activeEventSource.close();
          activeEventSource = null;
        }
        
        // Intentar reconectar si no hemos excedido el número máximo de intentos
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttempts++;
          console.log(`ChatWindow (${props.sessionId}): Reconnecting... Attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`);
          
          // Mostrar mensaje de reconexión
          if (!currentResponse.value.includes('Reconectando')) {
            currentResponse.value += currentResponse.value ? '\n\nReconectando al servidor...' : 'Reconectando al servidor...';
            scrollToBottom();
          }
          
          // Reconectar después de un breve retraso
          setTimeout(() => {
            // Verificar que aún estamos en modo streaming *después* del retraso
            if (isStreaming.value) {
              console.log(`ChatWindow (${props.sessionId}): Attempting reconnect after delay.`);
              activeEventSource = createEventSourceWithRetry(props.sessionId);
              
              // Volver a configurar los manejadores
              if (activeEventSource) {
                activeEventSource.onmessage = activeEventSource.onmessage;
                activeEventSource.onerror = activeEventSource.onerror;
              }
            } else {
              console.log(`ChatWindow (${props.sessionId}): Not reconnecting, streaming is no longer active.`);
            }
          }, RECONNECT_DELAY);
        } else {
          // Hemos excedido el número máximo de intentos, mostrar mensaje de error
          isStreaming.value = false;
          
          if (currentResponse.value) { // Si había una respuesta parcial antes del error
            messages.value.push({ role: 'model', content: currentResponse.value + '\n\n[Error de conexión después de varios intentos]' });
            currentResponse.value = '';
          } else if (!messages.value.some(m => m.role === 'model' && m.content.includes('Error'))) {
            messages.value.push({ 
              role: 'model', 
              content: 'Error de conexión con el servidor después de varios intentos. Por favor, intenta nuevamente más tarde.' 
            });
          }
          scrollToBottom();
        }
      } else {
        // If isStreaming is false, this onerror is likely the natural closure after DONE.
        console.log(`ChatWindow (${props.sessionId}): EventSource closed naturally after streaming.`);
      }
    };
  } catch (error) {
    console.error(`ChatWindow (${props.sessionId}): Error in sendMessage try block:`, error);
    messages.value.push({ role: 'model', content: 'Error crítico al enviar el mensaje.' });
    isStreaming.value = false;
  }
};

const formatMessage = (content: string) => {
  if (!content) return '';
  const escapeHtml = (unsafe: string) => unsafe.replace(/&/g, "&").replace(/</g, "<").replace(/>/g, ">").replace(/"/g, "").replace(/'/g, "'");
  let safeContent = escapeHtml(content);
  safeContent = safeContent.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" class="text-ch-accent hover:underline">$1</a>');
  return safeContent.replace(/\n/g, '<br>');
};

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

const sendButtonDisabled = computed(() => (!userMessage.value.trim() && !isFileUploaded.value) || isStreaming.value || componentLoading.value);

</script>

<style scoped>
.transform.rotate-45 {
  transform: rotate(45deg);
}
textarea {
  min-height: 46px; 
  max-height: 120px; 
  overflow-y: hidden; 
}

/* Animaciones para mensajes y burbujas de chat */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in {
  animation: fadeIn 0.3s ease-out forwards;
}

/* Animaciones para los puntos de carga */
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

.animate-bounce-delay-1 {
  animation: bounce 1s infinite;
}

.animate-bounce-delay-2 {
  animation: bounce 1s infinite;
  animation-delay: 0.2s;
}

.animate-bounce-delay-3 {
  animation: bounce 1s infinite;
  animation-delay: 0.4s;
}

/* Efectos de hover para las burbujas */
.transform.hover\:scale-\[101\%\]:hover {
  transition: transform 0.2s ease;
}
</style>
