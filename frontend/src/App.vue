<template>
  <div class="min-h-screen bg-gray-100">
    <header class="bg-blue-600 text-white p-4 shadow-md">
      <div class="container mx-auto flex items-center">
        <h1 class="text-xl font-bold">Gemini Chat</h1>
      </div>
    </header>
    
    <main class="container mx-auto mt-8 px-4">
      <div class="max-w-4xl mx-auto bg-white rounded-lg shadow-md overflow-hidden">
        <div class="p-4">
          <ChatWindow />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import ChatWindow from './components/ChatWindow.vue'
</script>
