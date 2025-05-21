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
          {{ activeSessionId ? `Chat ${activeSessionId.substring(0, 8)}...` : 'Gemini Chat' }}
        </h1>
      </header>

      <main class="flex-grow overflow-hidden bg-ch-bg-chat-area">
        <!-- Importante: ChatWindow solo se renderiza si activeSessionId es una cadena no vacía -->
        <ChatWindow
          v-if="activeSessionId && typeof activeSessionId === 'string' && activeSessionId.length > 0"
          :key="activeSessionId" 
          :session-id="activeSessionId"
          class="h-full"
        />
        <div v-else class="h-full flex flex-col items-center justify-center text-ch-text-secondary p-8">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-16 h-16 mb-4">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 9.75a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375m-13.5 3.01c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.184-4.183a1.14 1.14 0 01.778-.332 48.294 48.294 0 005.83-.498c1.585-.233 2.708-1.626 2.708-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
          </svg>
          <p class="text-xl">Selecciona un chat o crea uno nuevo para comenzar.</p>
          <button @click="triggerNewSessionCreation" class="mt-6 px-4 py-2 bg-ch-accent text-white rounded-lg hover:bg-opacity-80">
            Crear Nuevo Chat
          </button>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import ChatHistoryPanel from './components/ChatHistoryPanel.vue'
import ChatWindow from './components/ChatWindow.vue'
import { chatService } from './services/chatService'

const activeSessionId = ref<string | null>(null)
console.log('App.vue: script setup evaluated, activeSessionId initial:', activeSessionId.value);


const loadAndSetInitialSession = () => {
  console.log('App.vue: loadAndSetInitialSession called');
  // Inicializar explícitamente el servicio chat
  chatService.initialize();
  
  const initialId = chatService.getActiveSession(); 
  console.log('App.vue: chatService.getActiveSession() returned:', initialId);
  if (initialId) {
    activeSessionId.value = initialId;
    chatService.setActiveSession(initialId); // Asegurar que el servicio también lo sepa
    console.log('App.vue: activeSessionId set to (from initial load):', activeSessionId.value);
  } else {
    console.log('App.vue: No initial active session ID found.');
    // Opcional: crear una sesión si no existe ninguna
    // triggerNewSessionCreation(); 
  }
};

const handleSelectSession = (sessionId: string) => {
  console.log('App.vue: handleSelectSession triggered with sessionId:', sessionId);
  chatService.setActiveSession(sessionId)
  activeSessionId.value = sessionId
  console.log('App.vue: activeSessionId set to (from select):', activeSessionId.value);
}

const handleSessionCreated = (newSessionId: string) => {
  console.log('App.vue: handleSessionCreated triggered with newSessionId:', newSessionId);
  chatService.setActiveSession(newSessionId); 
  activeSessionId.value = newSessionId 
  console.log('App.vue: activeSessionId set to (from created):', activeSessionId.value);
}

const handleSessionDeleted = (deletedSessionId: string, wasActive: boolean) => {
  console.log('App.vue: handleSessionDeleted triggered for sessionId:', deletedSessionId, 'wasActive:', wasActive);
  if (wasActive || activeSessionId.value === deletedSessionId) {
    const remainingSessions = chatService.getAllSessionIds();
    if (remainingSessions.length > 0) {
      const newActive = remainingSessions[0];
      chatService.setActiveSession(newActive);
      activeSessionId.value = newActive;
      console.log('App.vue: activeSessionId set to (after delete, new active):', activeSessionId.value);
    } else {
      chatService.setActiveSession(null);
      activeSessionId.value = null;
      console.log('App.vue: activeSessionId set to null (after delete, no sessions left)');
    }
  }
};


const triggerNewSessionCreation = async () => {
  console.log('App.vue: triggerNewSessionCreation called');
  try {
    const newSessionId = await chatService.createSession();
    console.log('App.vue: New session created by trigger:', newSessionId);
    // ChatHistoryPanel debería actualizarse por su cuenta al leer de localStorage
    // Solo necesitamos asegurarnos de que la nueva sesión se active aquí.
    await nextTick(); 
    handleSessionCreated(newSessionId); // Esto establecerá activeSessionId y notificará al servicio
  } catch (error) {
    console.error("App.vue: Error creando nueva sesión desde trigger:", error);
    alert("No se pudo crear una nueva sesión.");
  }
};


onMounted(() => {
  console.log('App.vue: onMounted triggered');
  loadAndSetInitialSession();
})
</script>

<style scoped>
.flex-shrink-0 {
  flex-shrink: 0;
}
</style>
