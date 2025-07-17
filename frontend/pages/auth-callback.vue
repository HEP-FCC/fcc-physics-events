<template>
    <div class="auth-callback-page">
        <div v-if="isLoading" class="loading">
            <h2>Processing authentication...</h2>
            <p>Please wait while we complete your login.</p>
        </div>

        <div v-else-if="error" class="error">
            <h2>Authentication Failed</h2>
            <p>{{ error }}</p>
            <button @click="redirectToHome" class="retry-btn">Return to Home</button>
        </div>

        <div v-else class="success">
            <h2>Authentication Successful!</h2>
            <p>You have been successfully logged in. Redirecting...</p>
        </div>
    </div>
</template>

<script setup lang="ts">
const route = useRoute();
const router = useRouter();

const isLoading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
    try {
        // Check for error in query params
        const errorParam = route.query.error as string;
        if (errorParam) {
            error.value = "Authentication failed. Please try again.";
            isLoading.value = false;
            return;
        }

        // Get the authorization code from query params (backend/CERN auth service redirects here after login)
        const code = route.query.code as string;
        const state = route.query.state as string;

        // Call your backend /auth endpoint with the code
        const response = await fetch(`http://localhost:8000/auth?code=${code}&state=${state}`, {
            method: "GET",
            credentials: "include",
        });

        const data = await response.json();

        if (data.error) {
            error.value = data.error;
        }

        // Save JWT token as cookie
        const cookie = useCookie("fcc-physics-events-web", {
            maxAge: 60 * 60 * 24, // 1 day as CERN's tokens also expire in that time
            httpOnly: false,
            secure: true,
            sameSite: "lax", // TODO: check wtat does this mean
        });

        cookie.value = data;

        // Redirect to home after successful authentication
        setTimeout(() => {
            router.push("/");
        }, 300);
    } catch (err) {
        console.error("Auth callback error:", err);
        error.value = "An error occurred during authentication.";
    } finally {
        isLoading.value = false;
    }
});

function redirectToHome() {
    router.push("/");
}
</script>
<style scoped>
.auth-callback-page {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: 2rem;
    font-family: system-ui, sans-serif;
}

.loading,
.error,
.success {
    text-align: center;
    max-width: 400px;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.loading {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
}

.error {
    background: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
}

.success {
    background: #d1edff;
    border: 1px solid #bee5eb;
    color: #0c5460;
}

.retry-btn {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
}

.retry-btn:hover {
    background: #0052a3;
}

h2 {
    margin-bottom: 1rem;
}

p {
    margin-bottom: 0.5rem;
}
</style>
