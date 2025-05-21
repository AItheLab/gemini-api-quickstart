// Gemini Chat Application with Vue 3
const { createApp, ref, onMounted, nextTick, watch } = Vue;

const app = createApp({
  setup() {
    // State management
    const userMessage = ref('');
    const messages = ref([]);
    const isLoading = ref(false);
    const chatHistory = ref([
      { title: 'ChatAI', id: 'chat1' },
      { title: 'Image of sun', id: 'chat2' },
      { title: 'Data Analyst', id: 'chat3' }
    ]);
    const selectedChatIndex = ref(0);
    const selectedFile = ref(null);
    const notification = ref({ 
      show: false, 
      message: '' 
    });
    
    // DOM references
    const messagesContainer = ref(null);
    const fileInput = ref(null);
    const messageInput = ref(null);
    
    // Fetch chat history on component mount
    onMounted(async () => {
      try {
        const response = await fetch('/get_history');
        const data = await response.json();
        if (data.success && data.history) {
          messages.value = data.history;
        }
        
        focusMessageInput();
      } catch (error) {
        console.error('Error fetching chat history:', error);
      }
    });
    
    // Methods
    const sendMessage = async () => {
      if (!userMessage.value.trim() && !selectedFile.value) return;
      
      // Add user message to chat
      const userContent = userMessage.value.trim();
      messages.value.push({
        role: 'user',
        content: userContent
      });
      
      // Clear input and scroll to bottom
      userMessage.value = '';
      await scrollToBottom();
      
      // Set loading state
      isLoading.value = true;
      
      try {
        // Prepare form data if there's a file
        let body;
        let endpoint = '/chat';
        
        if (selectedFile.value) {
          const formData = new FormData();
          formData.append('file', selectedFile.value);
          formData.append('message', userContent);
          
          // Upload file first
          const uploadResponse = await fetch('/upload', {
            method: 'POST',
            body: formData
          });
          
          const uploadResult = await uploadResponse.json();
          
          if (!uploadResult.success) {
            throw new Error(uploadResult.message || 'File upload failed');
          }
          
          body = JSON.stringify({ message: userContent });
          selectedFile.value = null;
        } else {
          body = JSON.stringify({ message: userContent });
        }
        
        // Send message to backend
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: body
        });
        
        const data = await response.json();
        
        if (data.success) {
          // Start listening for the stream response
          listenForStreamResponse();
        } else {
          throw new Error(data.message || 'Failed to send message');
        }
      } catch (error) {
        console.error('Error sending message:', error);
        isLoading.value = false;
        
        showNotification('Error: ' + (error.message || 'Failed to communicate with the server'));
      }
    };
    
    const listenForStreamResponse = () => {
      const eventSource = new EventSource('/stream');
      let modelResponse = '';
      let messageAdded = false;
      
      eventSource.onmessage = (event) => {
        if (!messageAdded) {
          // Add model response message placeholder
          messages.value.push({
            role: 'model',
            content: ''
          });
          messageAdded = true;
        }
        
        // Update the content as chunks arrive
        modelResponse += event.data;
        const lastMessage = messages.value[messages.value.length - 1];
        lastMessage.content = modelResponse;
        
        scrollToBottom();
      };
      
      eventSource.onerror = () => {
        eventSource.close();
        isLoading.value = false;
        
        // If we never received any message, show an error
        if (!messageAdded) {
          showNotification('Error: No response received from Gemini');
        }
      };
    };
    
    const scrollToBottom = async () => {
      await nextTick();
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
      }
    };
    
    const startNewChat = () => {
      // Add new chat to history
      chatHistory.value.unshift({
        title: 'New conversation',
        id: 'chat' + Date.now()
      });
      
      // Select the new chat
      selectedChatIndex.value = 0;
      
      // Clear messages
      messages.value = [];
      
      // Focus the input
      focusMessageInput();
    };
    
    const selectChat = (index) => {
      selectedChatIndex.value = index;
      // Here you would load the messages for the selected chat from the backend
      // For now, we'll just simulate that by clearing the messages
      messages.value = [];
    };
    
    const triggerFileUpload = () => {
      if (fileInput.value) {
        fileInput.value.click();
      }
    };
    
    const handleFileUpload = (event) => {
      const file = event.target.files[0];
      if (!file) return;
      
      const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg'];
      
      if (!allowedTypes.includes(file.type)) {
        showNotification('Only JPEG and PNG images are supported');
        return;
      }
      
      selectedFile.value = file;
      focusMessageInput();
    };
    
    const removeFile = () => {
      selectedFile.value = null;
      if (fileInput.value) {
        fileInput.value.value = '';
      }
      focusMessageInput();
    };
    
    const showNotification = (message, duration = 3000) => {
      notification.value = {
        show: true,
        message
      };
      
      setTimeout(() => {
        notification.value.show = false;
      }, duration);
    };
    
    const focusMessageInput = () => {
      nextTick(() => {
        if (messageInput.value) {
          messageInput.value.focus();
        }
      });
    };
    
    // Watch for changes to automatically resize textarea
    watch(userMessage, () => {
      nextTick(() => {
        if (messageInput.value) {
          messageInput.value.style.height = 'auto';
          messageInput.value.style.height = messageInput.value.scrollHeight + 'px';
        }
      });
    });
    
    return {
      userMessage,
      messages,
      isLoading,
      chatHistory,
      selectedChatIndex,
      selectedFile,
      notification,
      messagesContainer,
      fileInput,
      messageInput,
      sendMessage,
      startNewChat,
      selectChat,
      triggerFileUpload,
      handleFileUpload,
      removeFile
    };
  }
});

app.mount('#app');
