<template>
    <div class="auth-section">
        <!-- Authentication controls -->
        <div v-if="!isAuthenticated" class="login-section">
            <button @click="handleLogin" :disabled="isLoading" class="login-btn">
                {{ isLoading ? "Logging in..." : "Login with CERN" }}
            </button>
        </div>

        <div v-else class="user-section">
            <div class="user-info">
                <span class="user-name">{{ user?.name || user?.preferred_username || "User" }}</span>
                <span class="user-email">{{ user?.email }}</span>
            </div>
            <button @click="handleLogout" :disabled="isLoading" class="logout-btn">
                {{ isLoading ? "Logging out..." : "Logout" }}
            </button>
        </div>

        <!-- Error message -->
        <div v-if="error" class="error-message">
            {{ error }}
            <button @click="clearError" class="clear-error-btn">×</button>
        </div>
    </div>
</template>

<script setup lang="ts">
const { authState, login, logout, clearError, checkAuthStatus } = useAuth();

// Computed properties for easy access
const isAuthenticated = computed(() => authState.value.isAuthenticated);
const user = computed(() => authState.value.user);
const isLoading = computed(() => authState.value.isLoading);
const error = computed(() => authState.value.error);

// Handle login
function handleLogin() {
    login();
}

// Handle logout
async function handleLogout() {
    await logout();
}

// Check auth status on component mount
onMounted(async () => {
    await checkAuthStatus();
});
</script>

<style scoped>
.auth-section {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.5rem;
}

.login-section {
    display: flex;
    align-items: center;
}

.login-btn {
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 0.5rem 1rem;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background-color 0.2s;
}

.login-btn:hover:not(:disabled) {
    background: #0052a3;
}

.login-btn:disabled {
    background: #ccc;
    cursor: not-allowed;
}

.user-section {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.user-info {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
}

.user-name {
    font-weight: 600;
    font-size: 0.9rem;
}

.user-email {
    font-size: 0.8rem;
    color: #666;
}

.logout-btn {
    background: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 0.4rem 0.8rem;
    cursor: pointer;
    font-size: 0.8rem;
    transition: background-color 0.2s;
}

.logout-btn:hover:not(:disabled) {
    background: #c82333;
}

.logout-btn:disabled {
    background: #ccc;
    cursor: not-allowed;
}

.error-message {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
    border-radius: 4px;
    padding: 0.5rem;
    font-size: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.clear-error-btn {
    background: none;
    border: none;
    color: #721c24;
    cursor: pointer;
    font-size: 1rem;
    line-height: 1;
    padding: 0;
    margin-left: auto;
}

.clear-error-btn:hover {
    color: #491217;
}
</style>
