<template>
    <UApp>
        <!-- Navigation Header -->
        <header class="dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50" style="background-color: var(--color-space-50)">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex items-center h-16 relative">
                    <!-- Left: Logo -->
                    <div class="flex items-center">
                        <NuxtLink to="/" class="flex items-center">
                            <NuxtImg src="/logo.png" alt="FCC Physics Events" class="h-8 w-auto" />
                        </NuxtLink>
                    </div>

                    <!-- Center: App Title -->
                    <div class="absolute left-1/2 transform -translate-x-1/2">
                        <h1 class="text-xl font-semibold text-gray-900 dark:text-gray-100 font-sans whitespace-nowrap">
                            {{ appTitle }}
                        </h1>
                    </div>

                    <!-- Right: Authentication Section -->
                    <div class="ml-auto">
                        <AuthSection />
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="pb-10" style="background-color: var(--color-space-50)">
            <NuxtPage />
        </main>

        <!-- Footer -->
        <AppFooter />
    </UApp>
</template>

<script setup lang="ts">
import AuthSection from "~/components/auth/AuthSection.vue";
import AppFooter from "~/components/AppFooter.vue";

// Auto-imported: useAuth, useDynamicNavigation, useAppConfiguration

// Check authentication status on app initialization
const { checkAuthStatus } = useAuth();
const { initializeNavigation } = useDynamicNavigation();
const { appTitle, mainTableDisplayName } = useAppConfiguration();

onMounted(async () => {
    // Initialize navigation configuration globally (early initialization for better UX)
    await initializeNavigation();

    // Check authentication status
    await checkAuthStatus();
});
</script>
