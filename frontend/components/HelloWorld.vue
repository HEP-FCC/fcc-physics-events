<script setup lang="ts">
import { ref, reactive, watch } from "vue";
import { watchDebounced } from "@vueuse/core";
import { getApiClient } from "../composables/getApiClient";
import type { Sample, PaginatedResponse } from "../types/sample";

const searchQuery = ref("");
const searchState = reactive({
    isLoading: false,
    events: [] as Sample[],
    error: null as string | null,
});
const pagination = reactive({
    currentPage: 1,
    pageSize: 20,
    totalEvents: 0,
});
const expandedRows = reactive(new Set<number>());

const apiClient = getApiClient();

async function performSearch() {
    if (!searchQuery.value.trim()) {
        searchState.events = [];
        pagination.totalEvents = 0;
        return;
    }

    searchState.isLoading = true;
    searchState.error = null;

    try {
        const offset = (pagination.currentPage - 1) * pagination.pageSize;
        const response: PaginatedResponse = await apiClient.searchSamples(
            searchQuery.value,
            pagination.pageSize,
            offset,
        );
        searchState.events = response.items;
        pagination.totalEvents = response.total;
    } catch (err) {
        searchState.error = err instanceof Error ? err.message : "Failed to fetch events.";
        searchState.events = [];
        pagination.totalEvents = 0;
    } finally {
        searchState.isLoading = false;
    }
}

// Toggle visibility of metadata details for a specific event
function toggleMetadata(processId: number) {
    if (expandedRows.has(processId)) {
        expandedRows.delete(processId);
    } else {
        expandedRows.add(processId);
    }
}

// Helper functions for metadata rendering
function isLongStringField(key: string, value: any): boolean {
    if (typeof value !== "string") return false;
    // Known long fields or strings longer than 50 characters
    const longFields = ["path", "software-stack", "description", "url", "command"];
    return longFields.includes(key.toLowerCase()) || value.length > 50;
}

function isShortField(key: string, value: any): boolean {
    if (typeof value === "number") return true;
    if (typeof value === "boolean") return true;
    if (typeof value === "string" && value.length <= 20) return true;
    return false;
}

function formatFieldName(key: string): string {
    return key.replace(/[-_]/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
}

// Sort and group metadata fields for consistent display
function getSortedMetadata(metadata: Record<string, any>) {
    const entries = Object.entries(metadata);

    // Filter out fields that are already displayed in the main event row
    const mainDisplayFields = new Set([
        "process-name",
        "detector_name",
        "framework_name",
        "campaign_name",
        "accelerator_name",
        "process_id",
    ]);
    const filteredEntries = entries.filter(([key]) => !mainDisplayFields.has(key));

    // Define the specific order: description first, comment second, software-stack and path at the end
    const priorityOrder = ["description", "comment"];
    const endOrder = ["software-stack", "path"];

    // Separate entries by priority
    const priorityFields: [string, any][] = [];
    const endFields: [string, any][] = [];
    const remainingFields: [string, any][] = [];

    filteredEntries.forEach(([key, value]) => {
        if (priorityOrder.includes(key)) {
            priorityFields.push([key, value]);
        } else if (endOrder.includes(key)) {
            endFields.push([key, value]);
        } else {
            remainingFields.push([key, value]);
        }
    });

    // Sort priority fields by their defined order
    priorityFields.sort(([a], [b]) => priorityOrder.indexOf(a) - priorityOrder.indexOf(b));

    // Sort remaining fields alphabetically
    remainingFields.sort(([a], [b]) => a.localeCompare(b));

    // Sort end fields by their defined order
    endFields.sort(([a], [b]) => endOrder.indexOf(a) - endOrder.indexOf(b));

    return [...priorityFields, ...remainingFields, ...endFields];
}

// Watch page changes to trigger search with new pagination offset
watch(() => pagination.currentPage, performSearch);

// Debounced search: reset to page 1 and search when query changes
watchDebounced(
    searchQuery,
    () => {
        if (pagination.currentPage === 1) {
            // Already on page 1, search directly
            performSearch();
        } else {
            // Reset to page 1 (triggers page watcher to search)
            pagination.currentPage = 1;
        }
    },
    { debounce: 500 },
);
</script>

<template>
    <UContainer class="py-4 sm:py-6 lg:py-8">
        <div class="space-y-6">
            <!-- Header Section -->
            <UCard>
                <template #header>
                    <h1 class="text-3xl font-bold">FCC Physics Events Search</h1>
                </template>

                <div class="space-y-4">
                    <UInput
                        v-model="searchQuery"
                        placeholder='e.g., detector:"IDEA" AND metadata.status="done"'
                        size="lg"
                        icon="i-heroicons-magnifying-glass"
                        class="w-full"
                    />

                    <UAlert
                        v-if="searchState.error"
                        color="red"
                        variant="soft"
                        icon="i-heroicons-exclamation-triangle"
                        :title="searchState.error"
                        description="Please check your query syntax and try again."
                        closable
                        @close="searchState.error = null"
                    />
                </div>
            </UCard>

            <!-- Loading State -->
            <UCard v-if="searchState.isLoading">
                <div class="space-y-4">
                    <USkeleton v-for="i in 5" :key="i" class="h-12 w-full" />
                </div>
            </UCard>

            <!-- Results Section -->
            <div v-else-if="searchState.events.length > 0" class="space-y-6">
                <!-- Top Pagination -->
                <div class="flex justify-between items-center">
                    <div class="text-sm text-gray-600">
                        Showing
                        <strong
                            >{{ (pagination.currentPage - 1) * pagination.pageSize + 1 }}-{{
                                Math.min(pagination.currentPage * pagination.pageSize, pagination.totalEvents)
                            }}</strong
                        >
                        of <strong>{{ pagination.totalEvents }}</strong> results
                    </div>
                    <UPagination
                        v-model:page="pagination.currentPage"
                        :total="pagination.totalEvents"
                        :items-per-page="pagination.pageSize"
                    />
                </div>

                <!-- Event Results -->
                <div class="space-y-2">
                    <UCard v-for="event in searchState.events" :key="event.process_id" class="overflow-hidden">
                        <!-- Compact Process Information Row -->
                        <div class="px-4 py-1">
                            <div class="flex items-center justify-between gap-4">
                                <!-- Left side: Process name and badges -->
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center gap-3 flex-wrap">
                                        <!-- Process Name -->
                                        <h3 class="font-semibold text-base text-gray-900 truncate min-w-0 flex-shrink">
                                            <span class="text-slate-500">Process:</span>
                                            <span class="ml-1 text-gray-900">{{ event.name }}</span>
                                        </h3>

                                        <!-- Compact badges in a single row -->
                                        <div class="flex items-center gap-3 flex-wrap">
                                            <UBadge v-if="event.detector_name" color="blue" variant="subtle" size="s">
                                                <span class="text-blue-600">Detector:</span>
                                                <span class="ml-1">{{ event.detector_name }}</span>
                                            </UBadge>
                                            <UBadge v-if="event.framework_name" color="green" variant="subtle" size="s">
                                                <span class="text-green-600">Framework:</span>
                                                <span class="ml-1">{{ event.framework_name }}</span>
                                            </UBadge>
                                            <UBadge v-if="event.campaign_name" color="amber" variant="subtle" size="s">
                                                <span class="text-amber-600">Campaign:</span>
                                                <span class="ml-1">{{ event.campaign_name }}</span>
                                            </UBadge>
                                            <UBadge
                                                v-if="event.accelerator_name"
                                                color="purple"
                                                variant="subtle"
                                                size="s"
                                            >
                                                <span class="text-purple-600">Accelerator:</span>
                                                <span class="ml-1">{{ event.accelerator_name }}</span>
                                            </UBadge>
                                        </div>
                                    </div>
                                </div>

                                <!-- Right side: Expand button -->
                                <UButton
                                    :icon="
                                        expandedRows.has(event.process_id)
                                            ? 'i-heroicons-chevron-up'
                                            : 'i-heroicons-chevron-down'
                                    "
                                    color="gray"
                                    variant="ghost"
                                    size="sm"
                                    :aria-label="`${
                                        expandedRows.has(event.process_id) ? 'Hide' : 'Show'
                                    } metadata for ${event.name}`"
                                    @click="toggleMetadata(event.process_id)"
                                />
                            </div>
                        </div>

                        <!-- Expandable Metadata Section -->
                        <div v-if="expandedRows.has(event.process_id)" class="border-t border-gray-200 bg-gray-50">
                            <div class="p-4">
                                <div class="space-y-3">
                                    <!-- Special handling for description and comment - show side by side -->
                                    <div
                                        v-if="event.metadata.description || event.metadata.comment"
                                        class="grid gap-3"
                                        :class="
                                            event.metadata.description && event.metadata.comment
                                                ? 'grid-cols-2'
                                                : 'grid-cols-1'
                                        "
                                    >
                                        <div v-if="event.metadata.description" class="space-y-1">
                                            <label class="text-sm font-medium text-gray-700">Description</label>
                                            <div class="bg-white rounded border px-2 py-1">
                                                <span class="text-sm text-gray-800">{{
                                                    event.metadata.description
                                                }}</span>
                                            </div>
                                        </div>
                                        <div v-if="event.metadata.comment" class="space-y-1">
                                            <label class="text-sm font-medium text-gray-700">Comment</label>
                                            <div class="bg-white rounded border px-2 py-1">
                                                <span class="text-sm text-gray-800">{{ event.metadata.comment }}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Render remaining metadata fields intelligently based on content -->
                                    <template v-for="[key, value] in getSortedMetadata(event.metadata)" :key="key">
                                        <!-- Skip description and comment as they're handled above -->
                                        <template v-if="key !== 'description' && key !== 'comment'">
                                            <!-- Long string fields (path, software-stack) - full width -->
                                            <div v-if="isLongStringField(key, value)" class="space-y-1">
                                                <label class="text-sm font-medium text-gray-700 capitalize">
                                                    {{ formatFieldName(key) }}
                                                </label>
                                                <div class="bg-white rounded border p-2">
                                                    <code class="text-xs text-gray-800 break-all">{{ value }}</code>
                                                </div>
                                            </div>

                                            <!-- Short fields - compact badge style with larger font -->
                                            <div v-else-if="isShortField(key, value)" class="inline-block mr-3 mb-2">
                                                <UBadge color="gray" variant="soft" size="md">
                                                    <span class="text-gray-600 font-medium text-sm"
                                                        >{{ formatFieldName(key) }}:</span
                                                    >
                                                    <span class="ml-1 font-normal text-sm">{{ value }}</span>
                                                </UBadge>
                                            </div>

                                            <!-- Medium fields - semi-compact -->
                                            <div v-else class="space-y-1">
                                                <label class="text-sm font-medium text-gray-700 capitalize">
                                                    {{ formatFieldName(key) }}
                                                </label>
                                                <div class="bg-white rounded border px-2 py-1">
                                                    <span class="text-sm text-gray-800">{{ value }}</span>
                                                </div>
                                            </div>
                                        </template>
                                    </template>
                                </div>
                            </div>
                        </div>
                    </UCard>
                </div>

                <!-- Bottom Pagination -->
                <div class="flex justify-center">
                    <UPagination
                        v-model:page="pagination.currentPage"
                        :total="pagination.totalEvents"
                        :items-per-page="pagination.pageSize"
                    />
                </div>
            </div>

            <!-- Empty State -->
            <UCard v-else class="text-center py-12">
                <div class="space-y-3">
                    <div class="text-4xl">🔍</div>
                    <h3 class="text-lg font-semibold text-gray-900">No events found</h3>
                    <p class="text-gray-500">Enter a query above to begin searching for physics events.</p>
                </div>
            </UCard>
        </div>
    </UContainer>
</template>
