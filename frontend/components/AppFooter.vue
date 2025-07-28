<template>
    <footer class="fixed bottom-0 left-0 right-0 border-t border-space-200 z-40 bg-space-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-center items-center h-6 text-xs">
                <span>© CERN {{ currentYear }} </span>
                <span class="mx-2">•</span>
                <a
                    href="https://github.com/HEP-FCC/fcc-physics-events"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="transition-colors duration-200"
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
