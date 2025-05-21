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

    <!-- Barra de búsqueda (funcionalidad opcional) -->
    <div class="relative">
      <input
        type="text"
        placeholder="Buscar chats..."
        class="w-full ch-input-field !bg-ch-bg-darkest !border-ch-border pl-8 text-sm"
        v-model="searchTerm"
      />
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4 absolute left-2 top-1/2 -translate-y-1/2 text-ch-icon">
        <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
      </svg>
    </div>

    <div class="flex-grow overflow-y-auto space-y-1 pr-1">
      <p v-if="filteredSessions.length === 0 && !loading" class="text-ch-text-secondary text-sm px-2 py-4 text-center">
        No hay chats. <br/> ¡Crea uno nuevo para empezar!
      </p>
      <div
        v-for="sessionId in filteredSessions"
        :key="sessionId"
        @click="$emit('selectSession', sessionId)"
        :class="[
          'p-2.5 rounded-lg cursor-pointer hover:bg-ch-bg-input group',
          isActiveSession(sessionId) ? 'bg-ch-accent/20' : ''
        ]"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <!-- Placeholder para Avatar -->
            <div class="w-8 h-8 bg-ch-bubble-other rounded-full flex items-center justify-center text-ch-text-primary text-sm">
              {{ sessionId.substring(0, 2).toUpperCase() }}
            </div>
            <span class="text-sm font-medium group-hover:text-ch-text-primary" :class="isActiveSession(sessionId) ? 'text-ch-accent' : 'text-ch-text-secondary'">
              Chat {{ sessionId.substring(0, 6) }}...
            </span>
          </div>
          <button
            @click.stop="confirmDeleteSession(sessionId)"
            title="Eliminar Chat"
            class="p-1 text-ch-icon opacity-0 group-hover:opacity-100 hover:text-ch-destructive rounded-md hover:bg-ch-destructive/20 transition-opacity"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12.56 0c1.153 0 2.24.032 3.287.094M5.116 5.79l-.05_1_316_269L3.37_4._15_8a2.25 2.25 0 012.244-2.077h8.584a2.25 2.25 0 012.244 2.077L18.884 5.79M15 5.79V4.5A2.25 2.25 0 0012.75 2.25h-1.5A2.25 2.25 0 009 4.5v1.29m0 0A48.65 48.65 0 0112 5.5c2.628 0 5.135-.433 7.388-1.217M5.002 5.5A48.294 48.294 0 0112 5.5c2.628 0 5.135-.433 7.388-1.217" />
            </svg>
          </button>
        </div>
      </div>
       <div v-if="loading" class="text-ch-text-secondary text-sm p-2">Cargando chats...</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, defineEmits, defineProps } from 'vue'
import { chatService } from '../services/chatService'

const props = defineProps<{
  activeSessionId: string | null
}>()

const emit = defineEmits(['selectSession', 'sessionCreated', 'sessionDeleted'])

const sessions = ref<string[]>([])
const loading = ref(true)
const searchTerm = ref('')

const loadSessions = () => {
  loading.value = true
  sessions.value = chatService.getAllSessionIds()
  loading.value = false
}

const filteredSessions = computed(() => {
  if (!searchTerm.value.trim()) {
    return sessions.value
  }
  return sessions.value.filter(id =>
    `Chat ${id.substring(0, 6)}...`.toLowerCase().includes(searchTerm.value.toLowerCase())
  )
})

const createNewSession = async () => {
  try {
    const newSessionId = await chatService.createSession()
    loadSessions() // Recargar la lista
    emit('sessionCreated', newSessionId) // Emitir para que App.vue lo seleccione
  } catch (error) {
    console.error("Error creando nueva sesión:", error)
    alert("No se pudo crear una nueva sesión.")
  }
}

const confirmDeleteSession = (sessionId: string) => {
  if (window.confirm(`¿Estás seguro de que quieres eliminar el chat ${sessionId.substring(0,6)}...? Esta acción no se puede deshacer.`)) {
    deleteSession(sessionId);
  }
}

const deleteSession = (sessionId: string) => {
  chatService.removeSession(sessionId);
  const oldSessions = [...sessions.value];
  loadSessions(); // Recargar la lista
  emit('sessionDeleted', sessionId, oldSessions.find(s => s === sessionId) === props.activeSessionId);
}


const isActiveSession = (sessionId: string) => {
  return props.activeSessionId === sessionId
}

onMounted(() => {
  loadSessions()
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