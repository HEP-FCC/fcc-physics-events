<template>
    <UApp>
        <!-- Navigation Header -->
        <header class="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center h-16">
                    <!-- Logo/Title -->
                    <div class="flex items-center">
                        <h1 class="text-xl font-semibold text-gray-900 dark:text-gray-100">FCC Physics Events</h1>
                    </div>

                    <!-- Navigation Links -->
                    <nav class="hidden md:flex space-x-8">
                        <NuxtLink
                            to="/"
                            class="text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100 px-3 py-2 text-sm font-medium"
                        >
                            {{ mainTableDisplayName }}
                        </NuxtLink>
                    </nav>

                    <!-- Authentication Section -->
                    <AuthSection />
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="pb-10">
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
const { mainTableDisplayName } = useAppConfiguration();

onMounted(async () => {
    // Initialize navigation configuration globally (early initialization for better UX)
    await initializeNavigation();

    // Check authentication status
    await checkAuthStatus();
});
</script>
