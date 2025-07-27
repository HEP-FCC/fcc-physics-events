<template>
    <div class="space-y-2">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Search Query
            <span v-if="showFilterNote" class="text-xs text-gray-600 dark:text-gray-400 ml-1">
                (Additional filters from navigation applied automatically)
            </span>
        </label>
        <div class="flex gap-2 items-center">
            <div class="flex-grow relative">
                <UInput
                    v-model="searchQuery"
                    :placeholder="searchPlaceholderText"
                    size="lg"
                    icon="i-heroicons-magnifying-glass"
                    class="pr-7 w-full"
                    @keydown.enter="$emit('search')"
                />
                <UTooltip
                    class="absolute right-1 top-1/2 transform -translate-y-1/2 z-10"
                    :content="{ side: 'top', sideOffset: 8 }"
                >
                    <template #content>
                        <div
                            class="max-w-md p-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg"
                        >
                            <div class="font-semibold text-sm mb-3 text-gray-900 dark:text-gray-100">
                                Query Language Help
                            </div>
                            <div class="text-xs text-gray-700 dark:text-gray-300 space-y-3">
                                <div>
                                    <div class="font-medium mb-2 text-gray-800 dark:text-gray-200">
                                        Example search queries:
                                    </div>
                                    <div class="space-y-1.5">
                                        <div>
                                            <code :class="codeClass">"H to cu"</code>
                                            - Filter by any field containing this string
                                        </div>
                                        <div>
                                            <code :class="codeClass">metadata.description:"ee -> Z(nu nu)"</code>
                                            - Metadata text field
                                        </div>
                                        <div>
                                            <code :class="codeClass">metadata.sum-of-weights>100000</code>
                                            - Metadata number filter
                                        </div>
                                    </div>
                                </div>
                                <div>
                                    <div class="font-medium mb-2 text-gray-800 dark:text-gray-200">
                                        Boolean Operators:
                                    </div>
                                    <div class="flex flex-wrap gap-1">
                                        <code :class="codeClass">AND</code>
                                        <code :class="codeClass">OR</code>
                                        <code :class="codeClass">NOT</code>
                                    </div>
                                </div>
                                <div>
                                    <div class="font-medium mb-2 text-gray-800 dark:text-gray-200">
                                        Comparison Operators:
                                    </div>
                                    <div class="flex flex-wrap gap-1">
                                        <code :class="codeClass">=</code>
                                        <code :class="codeClass">!=</code>
                                        <code :class="codeClass">&gt;</code>
                                        <code :class="codeClass">&lt;</code>
                                        <code :class="codeClass">&gt;=</code>
                                        <code :class="codeClass">&lt;=</code>
                                    </div>
                                    <div class="text-xs text-gray-600 dark:text-gray-400 mt-2">
                                        <div>
                                            <code :class="codeClass">:</code>
                                            substring,
                                            <code :class="codeClass">=~</code>
                                            regex match,
                                            <code :class="codeClass">!~</code>
                                            regex not match,
                                            <code :class="codeClass">:*</code>
                                            field exists
                                        </div>
                                    </div>
                                </div>
                                <div class="pt-2 border-t border-gray-200 dark:border-gray-600 text-center">
                                    <a
                                        href="https://cloud.google.com/logging/docs/view/logging-query-language"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        class="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 cursor-pointer hover:underline text-xs font-medium transition-colors inline-flex items-center gap-1"
                                    >
                                        View Full Documentation
                                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path
                                                stroke-linecap="round"
                                                stroke-linejoin="round"
                                                stroke-width="2"
                                                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                                            />
                                        </svg>
                                    </a>
                                </div>
                            </div>
                        </div>
                    </template>
                    <UButton
                        icon="i-heroicons-information-circle"
                        color="neutral"
                        variant="ghost"
                        size="xl"
                        class="w-6 h-6 p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full flex items-center justify-center"
                        @click="openQueryDocumentation"
                    />
                </UTooltip>
            </div>
            <UButton
                icon="i-heroicons-magnifying-glass"
                color="primary"
                variant="solid"
                size="lg"
                class="cursor-pointer"
                @click="$emit('search')"
            >
                Search
            </UButton>
            <div class="relative">
                <UTooltip text="Copy link" placement="top" class="cursor-pointer">
                    <template #default>
                        <UButton
                            icon="i-heroicons-link"
                            color="neutral"
                            variant="outline"
                            size="lg"
                            :loading="isPermalinkCopyInProgress"
                            :disabled="!canCopyLink"
                            @click="handleCopyPermalink"
                        />
                    </template>
                </UTooltip>
                <div
                    v-if="showLinkCopiedFeedback"
                    class="absolute -top-10 left-1/2 transform -translate-x-1/2 bg-green-600 text-white text-xs px-2 py-1 rounded shadow-lg whitespace-nowrap z-10"
                >
                    Link copied!
                </div>
            </div>
        </div>

        <UAlert
            v-if="searchError"
            color="error"
            variant="soft"
            icon="i-heroicons-exclamation-triangle"
            :title="searchError"
            description="Please check your query syntax and try again."
            closable
            @close="$emit('clearError')"
        />

        <UAlert
            v-if="!apiAvailable"
            color="warning"
            variant="soft"
            icon="i-heroicons-exclamation-triangle"
            title="API Server Unavailable"
            description="Unable to connect to the backend server. Please check if the server is running."
        />
    </div>
</template>

<script setup lang="ts">
interface Props {
    searchQuery: string;
    searchPlaceholderText: string;
    showFilterNote: boolean;
    canCopyLink: boolean;
    searchError: string | null;
    apiAvailable: boolean;
}

interface Emits {
    (e: "update:searchQuery", value: string): void;
    (e: "search" | "clearError"): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// Search query model with emit on update
const searchQuery = computed({
    get: () => props.searchQuery,
    set: (value: string) => emit("update:searchQuery", value),
});

// UI state for permalink functionality
const isPermalinkCopyInProgress = ref(false);
const showLinkCopiedFeedback = ref(false);
const codeClass = "bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-xs font-mono";

// Utility functions
const { copyToClipboard } = useUtils();

/**
 * Open external query documentation
 */
function openQueryDocumentation(): void {
    window.open("https://cloud.google.com/logging/docs/view/logging-query-language", "_blank");
}

/**
 * Show success notification for link copied
 */
function showSuccessNotification(): void {
    showLinkCopiedFeedback.value = true;
    setTimeout(() => {
        showLinkCopiedFeedback.value = false;
    }, 2000);
}

/**
 * Generate shareable permalink URL with current search state
 */
const generatePermalinkUrl = (): string => {
    const currentUrl = new URL(window.location.href);
    const params = new URLSearchParams();

    if (props.searchQuery.trim()) params.set("q", props.searchQuery.trim());

    const baseUrl = `${currentUrl.origin}${currentUrl.pathname}`;
    const queryString = params.toString();
    return queryString ? `${baseUrl}?${queryString}` : baseUrl;
};

/**
 * Handle permalink copy action with loading states
 */
async function handleCopyPermalink(): Promise<void> {
    if (isPermalinkCopyInProgress.value) return;

    try {
        isPermalinkCopyInProgress.value = true;
        const permalinkUrl = generatePermalinkUrl();
        await copyToClipboard(permalinkUrl);
        showSuccessNotification();
    } catch (error) {
        console.error("Failed to copy permalink:", error);
    } finally {
        isPermalinkCopyInProgress.value = false;
    }
}
</script>
