<template>
    <UApp>
        <!-- Navigation Header -->
        <header class="bg-space-50 border-space-200">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex items-center h-16">
                    <!-- Left: Logo -->
                    <div class="flex items-center">
                        <NuxtLink to="/" class="flex items-center">
                            <NuxtImg src="/logo.png" alt="FCC Physics Events" class="h-8 w-auto" />
                        </NuxtLink>
                    </div>

                    <!-- Center: App Title -->
                    <div class="absolute left-1/2 transform -translate-x-1/2">
                        <h1 class="text-xl font-semibold font-sans whitespace-nowrap">
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
const { appTitle, mainTableDisplayName } = useAppConfiguration();

onMounted(async () => {
    // Initialize navigation configuration globally (early initialization for better UX)
    await initializeNavigation();

    // Check authentication status
    await checkAuthStatus();
});
</script>
