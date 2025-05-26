<template>
  <div class="w-64 bg-ch-bg-panel h-full flex flex-col p-3 space-y-3">
    <div class="flex items-center justify-between mb-2">
      <h2 class="text-xl font-semibold text-ch-text-primary">Chats</h2>
      <button
        @click="createNewSession"
        title="Nuevo Chat"
        class="p-2 text-ch-icon hover:text-ch-accent hover:bg-ch-bg-input rounded-md"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
      </button>
    </div>

    <!-- Barra de búsqueda -->
    <div class="relative">
      <input
        type="text"
        placeholder="Buscar chats..."
        class="w-full ch-input-field !bg-ch-bg-darkest !border-ch-border pl-8 text-sm"
        v-model="searchTerm"
        @input="handleSearch"
      />
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4 absolute left-2 top-1/2 -translate-y-1/2 text-ch-icon">
        <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
      </svg>
    </div>

    <div class="flex-grow overflow-y-auto space-y-1 pr-1">
      <div v-if="loading" class="text-ch-text-secondary text-sm p-2 text-center">
        Cargando chats...
      </div>
      
      <p v-else-if="displayedChats.length === 0" class="text-ch-text-secondary text-sm px-2 py-4 text-center">
        <span v-if="searchTerm.trim()">
          No se encontraron chats para "<strong>{{ searchTerm }}</strong>"
        </span>
        <span v-else>
          No hay chats. <br/> ¡Crea uno nuevo para empezar!
        </span>
      </p>
      
      <div
        v-for="chat in displayedChats"
        :key="chat.session_id"
        @click="$emit('selectSession', chat.session_id)"
        :class="[
          'p-2.5 rounded-lg cursor-pointer hover:bg-ch-bg-input group',
          isActiveSession(chat.session_id) ? 'bg-ch-accent/20' : ''
        ]"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2 flex-grow min-w-0">
            <!-- Avatar con iniciales del título -->
            <div class="w-8 h-8 bg-ch-bubble-other rounded-full flex items-center justify-center text-ch-text-primary text-sm flex-shrink-0">
              {{ getInitials(chat.title) }}
            </div>
            
            <div class="flex-grow min-w-0">
              <!-- Título del chat -->
              <div class="text-sm font-medium group-hover:text-ch-text-primary truncate" 
                   :class="isActiveSession(chat.session_id) ? 'text-ch-accent' : 'text-ch-text-secondary'">
                {{ chat.title }}
              </div>
              
              <!-- Preview del último mensaje y metadatos -->
              <div class="text-xs text-ch-text-secondary/70 truncate mt-0.5">
                <span v-if="chat.last_message_preview">{{ chat.last_message_preview }}</span>
                <span v-else>{{ chat.message_count }} mensajes</span>
                
                <!-- Etiquetas -->
                <span v-if="chat.tags.length > 0" class="ml-1">
                  <span v-for="tag in chat.tags.slice(0, 2)" :key="tag" class="text-ch-accent text-xs">
                    #{{ tag }}
                  </span>
                  <span v-if="chat.tags.length > 2">...</span>
                </span>
              </div>
            </div>
          </div>
          
          <!-- Botones de acción -->
          <div class="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <!-- Pin -->
            <button
              v-if="chat.is_pinned"
              @click.stop="togglePin(chat.session_id)"
              title="Quitar de fijados"
              class="p-1 text-ch-accent hover:bg-ch-accent/20 rounded-md"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4">
                <path d="M10 1l3 3h4l-2 2-3-3-1 1 3 3-2 2-3-3-1 1 3 3-2 2-3-3-1 1 3 3-2 2-3-3v4l-3-3z"/>
              </svg>
            </button>
            
            <!-- Eliminar -->
            <button
              @click.stop="confirmDeleteSession(chat.session_id, chat.title)"
              title="Eliminar Chat"
              class="p-1 text-ch-icon hover:text-ch-destructive rounded-md hover:bg-ch-destructive/20"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12.56 0c1.153 0 2.24.032 3.287.094M5.116 5.79l-.05_1_316_269L3.37_4._15_8a2.25 2.25 0 012.244-2.077h8.584a2.25 2.25 0 012.244 2.077L18.884 5.79M15 5.79V4.5A2.25 2.25 0 0012.75 2.25h-1.5A2.25 2.25 0 009 4.5v1.29m0 0A48.65 48.65 0 0112 5.5c2.628 0 5.135-.433 7.388-1.217M5.002 5.5A48.294 48.294 0 0112 5.5c2.628 0 5.135-.433 7.388-1.217" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, defineEmits, defineProps, watch } from 'vue'
import { chatService } from '../services/chatService'

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

const props = defineProps<{
  activeSessionId: string | null
}>()

const emit = defineEmits(['selectSession', 'sessionCreated', 'sessionDeleted'])

const chats = ref<ChatMetadata[]>([])
const loading = ref(true)
const searchTerm = ref('')
const searchResults = ref<ChatMetadata[]>([])
const isSearching = ref(false)

// Computed para mostrar chats filtrados o resultados de búsqueda
const displayedChats = computed(() => {
  if (searchTerm.value.trim()) {
    return searchResults.value
  }

  // Ordenar chats: fijados primero, luego por fecha de actualización
  return [...chats.value].sort((a, b) => {
    if (a.is_pinned && !b.is_pinned) return -1
    if (!a.is_pinned && b.is_pinned) return 1
    return b.updated_at - a.updated_at
  })
})

const loadChats = async () => {
  loading.value = true
  try {
    chats.value = await chatService.getAllChats()
    console.log('Chats cargados desde backend:', chats.value.length)
  } catch (error) {
    console.error('Error cargando chats:', error)
    chats.value = []
  } finally {
    loading.value = false
  }
}

let searchTimeout: number | null = null

const handleSearch = async () => {
  const query = searchTerm.value.trim()
  
  // Limpiar timeout anterior
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  
  if (!query) {
    searchResults.value = []
    isSearching.value = false
    return
  }
  
  // Debounce la búsqueda
  searchTimeout = window.setTimeout(async () => {
    isSearching.value = true
    try {
      searchResults.value = await chatService.searchChats(query)
      console.log(`Búsqueda "${query}": ${searchResults.value.length} resultados`)
    } catch (error) {
      console.error('Error en búsqueda:', error)
      searchResults.value = []
    } finally {
      isSearching.value = false
    }
  }, 300)
}

const createNewSession = async () => {
  try {
    const newSessionId = await chatService.createSession()
    await loadChats() // Recargar la lista desde el backend
    emit('sessionCreated', newSessionId)
    console.log('Nueva sesión creada y lista actualizada')
  } catch (error) {
    console.error("Error creando nueva sesión:", error)
    alert("No se pudo crear una nueva sesión.")
  }
}

const confirmDeleteSession = (sessionId: string, title: string) => {
  if (window.confirm(`¿Estás seguro de que quieres eliminar "${title}"? Esta acción no se puede deshacer.`)) {
    deleteSession(sessionId)
  }
}

const deleteSession = async (sessionId: string) => {
  try {
    const success = await chatService.removeSession(sessionId)
    if (success) {
      const wasActive = props.activeSessionId === sessionId
      await loadChats() // Recargar desde backend
      emit('sessionDeleted', sessionId, wasActive)
      console.log(`Chat ${sessionId} eliminado y lista actualizada`)
    } else {
      alert('No se pudo eliminar el chat')
    }
  } catch (error) {
    console.error('Error eliminando chat:', error)
    alert('Error al eliminar el chat')
  }
}

const togglePin = async (sessionId: string) => {
  try {
    const success = await chatService.updateChatMetadata(sessionId, { toggle_pin: true })
    if (success) {
      await loadChats() // Recargar para ver el cambio
      console.log(`Pin toggle para chat ${sessionId}`)
    }
  } catch (error) {
    console.error('Error alternando pin:', error)
  }
}

const isActiveSession = (sessionId: string) => {
  return props.activeSessionId === sessionId
}

const getInitials = (title: string): string => {
  if (!title) return 'CH'
  
  const words = title.split(' ').filter(word => word.length > 0)
  if (words.length === 1) {
    return words[0].substring(0, 2).toUpperCase()
  }
  return words.slice(0, 2).map(word => word[0]).join('').toUpperCase()
}

// Limpiar timeout al desmontar
const cleanupSearch = () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
    searchTimeout = null
  }
}

onMounted(() => {
  loadChats()
  
  // Cleanup en caso de desmontaje
  return cleanupSearch
})
</script>

<style scoped>
/* Ajustes para el scrollbar dentro de este panel si es necesario */
.overflow-y-auto::-webkit-scrollbar {
  width: 4px;
}
.overflow-y-auto::-webkit-scrollbar-thumb {
  @apply bg-ch-border;
}
</style>