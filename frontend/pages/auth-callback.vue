<template>
    <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
        <div class="max-w-md w-full">
            <!-- Loading state -->
            <UCard v-if="isLoading" class="text-center">
                <template #header>
                    <div class="flex items-center justify-center gap-3">
                        <UIcon name="i-heroicons-arrow-path" class="w-6 h-6 animate-spin text-primary-500" />
                        <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">Authenticating</h2>
                    </div>
                </template>

                <p class="text-gray-600 dark:text-gray-400">
                    Please wait while we complete your login with CERN SSO...
                </p>

                <div class="mt-4">
                    <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div class="bg-primary-500 h-2 rounded-full animate-pulse" style="width: 60%" />
                    </div>
                </div>
            </UCard>

            <!-- Error state -->
            <UCard v-else-if="error" class="text-center">
                <template #header>
                    <div class="flex items-center justify-center gap-3">
                        <UIcon name="i-heroicons-exclamation-triangle" class="w-6 h-6 text-red-500" />
                        <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">Authentication Failed</h2>
                    </div>
                </template>

                <p class="text-gray-600 dark:text-gray-400 mb-6">
                    {{ error }}
                </p>

                <UButton color="primary" variant="solid" icon="i-heroicons-home" block @click="redirectToHome">
                    Return to Home
                </UButton>
            </UCard>

            <!-- Success state -->
            <UCard v-else class="text-center">
                <template #header>
                    <div class="flex items-center justify-center gap-3">
                        <UIcon name="i-heroicons-check-circle" class="w-6 h-6 text-green-500" />
                        <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">
                            Authentication Successful!
                        </h2>
                    </div>
                </template>

                <p class="text-gray-600 dark:text-gray-400 mb-4">You have been successfully logged in with CERN SSO.</p>

                <p class="text-sm text-gray-500 dark:text-gray-400">Redirecting you to the main application...</p>

                <div class="mt-4">
                    <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div class="bg-green-500 h-2 rounded-full transition-all duration-1000" style="width: 100%" />
                    </div>
                </div>
            </UCard>
        </div>
    </div>
</template>

<script setup lang="ts">
import { APP_CONFIG } from "~/config/app.config";

const route = useRoute();
const router = useRouter();
const { checkAuthStatus } = useAuth();

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
        const config = useRuntimeConfig();
        const response = await fetch(`${config.public.apiBaseUrl}/auth?code=${code}&state=${state}`, {
            method: "GET",
            credentials: "include", // Include credentials for auth endpoint
        });

        const data = await response.json();

        if (data.error) {
            error.value = data.error;
            isLoading.value = false;
            return;
        }

        // Save auth data as cookie (the backend already sets a session cookie,
        // but we also store the auth data for frontend use)
        const cookie = useCookie(APP_CONFIG.auth.cookieName, {
            maxAge: 60 * 60 * 24, // 1 day as CERN's tokens also expire in that time
            httpOnly: false,
            secure: process.env.NODE_ENV === "production", // Only secure in production
            sameSite: "lax",
        });

        cookie.value = data;

        // Update auth state immediately after setting cookie
        await checkAuthStatus();

        // Show success message briefly before redirect
        isLoading.value = false;

        // Redirect to home after successful authentication
        setTimeout(() => {
            router.push("/");
        }, 2000); // Slightly longer delay for better UX
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
