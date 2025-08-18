<template>
    <UApp class="min-h-screen flex flex-col">
        <!-- Navigation Header -->
        <header class="bg-space-50 border-space-200">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <!-- Mobile Layout (stacked) -->
                <div class="flex flex-col space-y-2 py-2 sm:hidden">
                    <!-- First row: Logo, Title, and Contact -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3 flex-1 min-w-0">
                            <NuxtLink to="/" class="flex items-center flex-shrink-0">
                                <NuxtImg src="/logo.png" alt="FCC Physics Events" class="h-8 w-auto" />
                            </NuxtLink>
                            <h1 class="text-lg font-semibold font-sans truncate">
                                {{ appTitle }}
                            </h1>
                        </div>
                        <div class="flex-shrink-0">
                            <ContactModal />
                        </div>
                    </div>
                    <!-- Second row: Authentication only -->
                    <div class="flex items-center justify-start">
                        <AuthSection />
                    </div>
                </div>

                <!-- Desktop Layout (single row) -->
                <div class="hidden sm:flex items-center h-16">
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

                    <!-- Right: Contact and Authentication Section -->
                    <div class="ml-auto flex items-center space-x-4">
                        <ContactModal />
                        <AuthSection />
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="flex-1">
            <NuxtPage />
        </main>

        <!-- Footer -->
        <AppFooter />
    </UApp>
</template>

<script setup lang="ts">
import AuthSection from "~/components/auth/AuthSection.vue";
import AppFooter from "~/components/AppFooter.vue";
import ContactModal from "~/components/ContactModal.vue";

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
