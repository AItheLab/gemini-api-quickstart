<template>
  <div class="min-h-screen bg-gray-100 flex flex-col">
    <header class="bg-blue-600 text-white p-4 shadow-md">
      <div class="container mx-auto flex items-center justify-between">
        <h1 class="text-xl font-bold">Gemini Chat</h1>
        <button @click="toggleSidebar" class="p-2 bg-blue-700 hover:bg-blue-800 rounded text-white focus:outline-none focus:ring-2 focus:ring-blue-400">
          <span v-if="isSidebarOpen">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
            </svg>
          </span>
          <span v-else>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
          </span>
        </button>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden relative"> <!-- Added relative for positioning context if needed -->
      <!-- Sidebar -->
      <aside 
        v-if="isSidebarOpen" 
        class="fixed inset-y-0 left-0 z-30 w-64 bg-gray-200 p-4 shadow-md transition-transform duration-300 ease-in-out transform md:relative md:translate-x-0 md:shadow-lg"
        :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full'"
      >
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-semibold">Sidebar</h2>
          <button @click="toggleSidebar" class="md:hidden p-1 text-gray-700 hover:text-gray-900 hover:bg-gray-300 rounded">
            <!-- Close icon for mobile sidebar -->
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <p>Sidebar Content</p>
        <!-- Add more sidebar content here -->
      </aside>

      <!-- Main content -->
      <main class="flex-1 p-4 overflow-y-auto" :class="{'md:ml-64': isSidebarOpen }">
        <div class="max-w-4xl mx-auto bg-white rounded-lg shadow-md overflow-hidden">
          <div class="p-4">
            <ChatWindow />
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import ChatWindow from './components/ChatWindow.vue'

const isSidebarOpen = ref(false) // Default to closed
const isMobile = ref(window.innerWidth < 768)

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value
}

const handleResize = () => {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value && !isSidebarOpen.value) {
    // Optional: Automatically open sidebar on desktop if it was closed
    // isSidebarOpen.value = true; 
  } else if (isMobile.value && isSidebarOpen.value) {
    // Optional: Automatically close sidebar if screen becomes mobile and sidebar is open
    // isSidebarOpen.value = false;
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  handleResize(); // Initial check
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

</script>
