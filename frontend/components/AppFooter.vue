<template>
    <footer
        class="fixed bottom-0 left-0 right-0 border-t border-gray-200 dark:border-gray-700 z-40"
        style="background-color: var(--color-space-50)"
    >
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-center items-center h-6 text-xs text-gray-500 dark:text-gray-400">
                <span>© CERN {{ currentYear }} </span>
                <span class="mx-2">•</span>
                <a
                    href="https://github.com/HEP-FCC/fcc-physics-events"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="hover:text-gray-700 dark:hover:text-gray-300 transition-colors duration-200"
                >
                    GitHub source
                </a>
            </div>
        </div>
    </footer>
</template>

<script setup lang="ts">
const currentYear = new Date().getFullYear();
</script>
