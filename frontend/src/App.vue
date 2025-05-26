<template>
  <div class="h-screen w-screen flex bg-ch-bg-darkest text-ch-text-primary overflow-hidden">
    <!-- Panel Izquierdo: Historial de Chats -->
    <ChatHistoryPanel
      :active-session-id="activeSessionId"
      @selectSession="handleSelectSession"
      @sessionCreated="handleSessionCreated"
      @sessionDeleted="handleSessionDeleted"
      class="flex-shrink-0"
    />

    <!-- Panel Central: Conversación Activa -->
    <div class="flex-grow flex flex-col h-full">
      <header class="bg-ch-bg-panel h-14 flex items-center px-6 border-b border-ch-border flex-shrink-0">
        <h1 class="text-lg font-semibold">
          {{ currentChatTitle || 'Gemini Chat' }}
        </h1>
      </header>

      <main class="flex-grow overflow-hidden bg-ch-bg-chat-area">
        <!-- ChatWindow solo se renderiza si hay una sesión activa -->
        <ChatWindow
          v-if="activeSessionId"
          :key="activeSessionId" 
          :session-id="activeSessionId"
          class="h-full"
        />
        <div v-else class="h-full flex flex-col items-center justify-center text-ch-text-secondary p-8">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-16 h-16 mb-4">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 9.75a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375m-13.5 3.01c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.184-4.183a1.14 1.14 0 01.778-.332 48.294 48.294 0 005.83-.498c1.585-.233 2.708-1.626 2.708-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
          </svg>
          <p class="text-xl">Envía un mensaje para empezar.</p>
          <p class="text-sm mt-2">O adjunta una imagen.</p>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import ChatHistoryPanel from './components/ChatHistoryPanel.vue'
import ChatWindow from './components/ChatWindow.vue'
import { chatService } from './services/chatService'

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

const activeSessionId = ref<string | null>(null)
const currentChatTitle = ref<string>('')
const availableChats = ref<ChatMetadata[]>([])

// Load available chats from backend
const loadAvailableChats = async () => {
  try {
    availableChats.value = await chatService.getAllChats()
    
    // If no active session but chats exist, select the most recent one
    if (!activeSessionId.value && availableChats.value.length > 0) {
      const mostRecentChat = availableChats.value[0] // Already sorted by date
      handleSelectSession(mostRecentChat.session_id)
    }
  } catch (error) {
    console.error('App: Error loading chats:', error)
    availableChats.value = []
  }
}

const handleSelectSession = (sessionId: string) => {
  chatService.setActiveSession(sessionId)
  activeSessionId.value = sessionId
  
  // Find the title of the selected chat
  const selectedChat = availableChats.value.find((chat: ChatMetadata) => chat.session_id === sessionId)
  currentChatTitle.value = selectedChat ? selectedChat.title : `Chat ${sessionId.substring(0, 8)}...`
}

const handleSessionCreated = async (newSessionId: string) => {
  chatService.setActiveSession(newSessionId)
  activeSessionId.value = newSessionId
  currentChatTitle.value = 'New chat' // Keep UI text in Spanish as per plan, but this is a default title
  
  // Reload chat list to include the new one
  await loadAvailableChats()
}

const handleSessionDeleted = async (deletedSessionId: string, wasActive: boolean) => {
  // Reload chats from backend
  await loadAvailableChats()
  
  if (wasActive || activeSessionId.value === deletedSessionId) {
    // If we delete the active session, select another or clear
    if (availableChats.value.length > 0) {
      const newActive = availableChats.value[0]
      handleSelectSession(newActive.session_id)
    } else {
      chatService.setActiveSession(null)
      activeSessionId.value = null
      currentChatTitle.value = ''
    }
  }
}

// Watcher to update title when active session changes
watch(activeSessionId, async (newSessionId: string | null) => {
  if (newSessionId) {
    // Find the updated chat title
    const chatData = availableChats.value.find((chat: ChatMetadata) => chat.session_id === newSessionId)
    if (chatData) {
      currentChatTitle.value = chatData.title
    } else {
      // If not found in cache, reload
      await loadAvailableChats()
      const updatedChat = availableChats.value.find((chat: ChatMetadata) => chat.session_id === newSessionId)
      currentChatTitle.value = updatedChat ? updatedChat.title : `Chat ${newSessionId.substring(0, 8)}...`
    }
  } else {
    currentChatTitle.value = ''
  }
})

onMounted(() => {
  console.log('App: Component mounted')
  chatService.initialize()
  loadAvailableChats()
})
</script>

<style scoped>
.flex-shrink-0 {
  flex-shrink: 0;
}
</style>
