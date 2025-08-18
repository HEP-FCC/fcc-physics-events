<template>
    <UModal v-model:open="isOpen" title="Contact & Resources">
        <UButton class="cursor-pointer" icon="i-heroicons-envelope" color="neutral" variant="ghost" label="Contact" @click="isOpen = true" />

        <template #body>
            <div class="space-y-6">
                <!-- Contact Email -->
                <div class="space-y-2">
                    <h3 class="text-sm font-medium text-deep-blue-900">Email</h3>
                    <div class="flex items-center space-x-2">
                        <UIcon name="i-heroicons-envelope" class="text-secondary-500" />
                        <a
                            href="mailto:FCC-PED-SoftwareAndComputing-Analysis@cern.ch"
                            class="text-deep-blue-600 hover:text-deep-blue-900 transition-colors"
                        >
                            FCC-PED-SoftwareAndComputing-Analysis
                        </a>
                    </div>
                </div>

                <!-- GitHub Source -->
                <div class="space-y-2">
                    <h3 class="text-sm font-medium text-deep-blue-900">Source Code</h3>
                    <div class="flex items-center space-x-2">
                        <UIcon name="i-heroicons-code-bracket" class="text-secondary-500" />
                        <a
                            href="https://github.com/HEP-FCC/fcc-physics-events"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="text-deep-blue-600 hover:text-deep-blue-900 transition-colors"
                        >
                            GitHub Repository
                        </a>
                    </div>
                </div>

                <!-- Forum -->
                <div class="space-y-2">
                    <h3 class="text-sm font-medium text-deep-blue-900">Community Forum</h3>
                    <div class="flex items-center space-x-2">
                        <UIcon name="i-heroicons-chat-bubble-left-right" class="text-secondary-500" />
                        <a
                            href="https://fccsw-forum.web.cern.ch/c/fccanalysis/9"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="text-deep-blue-600 hover:text-deep-blue-900 transition-colors"
                        >
                            Visit Forum
                        </a>
                    </div>
                </div>
            </div>
        </template>
    </UModal>
</template>

<script setup lang="ts">
const isOpen = ref(false);
</script>
