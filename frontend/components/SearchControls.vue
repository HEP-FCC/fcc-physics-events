<template>
    <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Search Query
            <span v-if="showFilterNote" class="text-xs text-gray-600 dark:text-gray-400 ml-1">
                (Additional filters from navigation applied automatically)
            </span>
        </label>
        <div class="flex gap-2 items-center">
            <UInput
                :model-value="modelValue"
                :placeholder="placeholder"
                size="lg"
                icon="i-heroicons-magnifying-glass"
                class="flex-1"
                @update:model-value="$emit('update:modelValue', $event)"
                @keydown.enter="handleSearch"
            />
            <UButton
                icon="i-heroicons-magnifying-glass"
                color="primary"
                variant="solid"
                size="lg"
                @click="handleSearch"
            >
                Search
            </UButton>
            <div class="relative">
                <UButton
                    icon="i-heroicons-link"
                    color="neutral"
                    variant="outline"
                    size="lg"
                    :loading="isCopiingLink"
                    :disabled="!canCopyLink"
                    @click="handleCopyPermalink"
                />
                <div
                    v-if="showCopiedNotification"
                    class="absolute -top-10 left-1/2 transform -translate-x-1/2 bg-green-600 text-white text-xs px-2 py-1 rounded shadow-lg whitespace-nowrap z-10"
                >
                    Link copied!
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { SearchControlsProps, SearchEvents } from "~/types/components";

const props = withDefaults(defineProps<SearchControlsProps & { modelValue: string }>(), {
    placeholder: "Search datasets...",
    showFilterNote: false,
    canCopyLink: false,
});

const emit = defineEmits<
    {
        "update:modelValue": [value: string];
        search: [];
    } & SearchEvents
>();

const isCopiingLink = ref(false);
const showCopiedNotification = ref(false);

function handleSearch() {
    emit("search");
}

// Helper function to show success notification
function showSuccessNotification() {
    showCopiedNotification.value = true;
    setTimeout(() => {
        showCopiedNotification.value = false;
    }, 2000);
}

// Fallback copy method for older browsers
function fallbackCopyToClipboard(text: string) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand("copy");
    document.body.removeChild(textArea);
}

async function handleCopyPermalink() {
    if (isCopiingLink.value) return;

    try {
        isCopiingLink.value = true;
        const permalinkUrl = props.generatePermalinkUrl();

        try {
            await navigator.clipboard.writeText(permalinkUrl);
        } catch {
            // Fallback for older browsers
            fallbackCopyToClipboard(permalinkUrl);
        }

        showSuccessNotification();
        emit("permalink-copied");
    } catch (error) {
        console.error("Failed to copy permalink:", error);
    } finally {
        isCopiingLink.value = false;
    }
}
</script>
