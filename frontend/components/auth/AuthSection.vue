<template>
    <div class="auth-section">
        <!-- Authentication controls -->
        <div v-if="!isAuthenticated" class="login-section">
            <UButton
                :loading="isLoading"
                color="primary"
                variant="solid"
                size="sm"
                icon="i-heroicons-user-circle"
                class="login-btn cursor-pointer"
                @click="handleLogin"
            >
                {{ isLoading ? "Signing in..." : "Sign in with CERN" }}
            </UButton>
        </div>

        <div v-else class="user-section">
            <div class="flex items-center gap-3">
                <div class="text-right">
                    <div class="text-sm font-medium">
                        {{ displayName }}
                    </div>
                    <div v-if="user?.preferred_username" class="text-xs">
                        {{ user.preferred_username }}
                    </div>
                </div>
                <UButton
                    :loading="isLoading"
                    color="error"
                    variant="outline"
                    size="sm"
                    icon="i-heroicons-arrow-right-on-rectangle"
                    @click="handleLogout"
                >
                    Sign out
                </UButton>
            </div>
        </div>

        <!-- Error alert -->
        <UAlert
            v-if="error"
            icon="i-heroicons-exclamation-triangle"
            color="error"
            variant="soft"
            :title="error"
            :close-button="{ icon: 'i-heroicons-x-mark-20-solid', color: 'gray', variant: 'link', padded: false }"
            class="fixed top-20 right-4 z-50 max-w-sm"
            @close="clearError"
        />
    </div>
</template>

<script setup lang="ts">
const { authState, login, logout, clearError } = useAuth();

// Computed properties for easy access
const isAuthenticated = computed(() => authState.value.isAuthenticated);
const user = computed(() => authState.value.user);
const isLoading = computed(() => authState.value.isLoading);
const error = computed(() => authState.value.error);

// Computed display name
const displayName = computed(() => {
    if (user.value?.given_name && user.value?.family_name) {
        return `${user.value.given_name} ${user.value.family_name}`;
    }
    return user.value?.preferred_username || "User";
});

// Handle login
function handleLogin() {
    login();
}

// Handle logout
async function handleLogout() {
    await logout();
}
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
