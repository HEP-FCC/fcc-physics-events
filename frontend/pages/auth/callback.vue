<template>
    <div class="flex items-center justify-center h-screen bg-gray-100 text-center">
        <div>
            <h1 class="text-xl font-semibold mb-2">Login Successful</h1>
            <p class="text-gray-600">This window will close automatically...</p>
        </div>
    </div>
</template>

<script setup>
import { onMounted } from "vue";

// Use the same channel name and message as the listener.
const AUTH_CHANNEL_NAME = "fcc-physics-auth-channel";
const AUTH_SUCCESS_MESSAGE = "authentication-successful";

onMounted(() => {
    // Use a BroadcastChannel to reliably notify other tabs.
    const authChannel = new BroadcastChannel(AUTH_CHANNEL_NAME);
    authChannel.postMessage(AUTH_SUCCESS_MESSAGE);
    authChannel.close();

    // Close this tab.
    window.close();
});
</script>
