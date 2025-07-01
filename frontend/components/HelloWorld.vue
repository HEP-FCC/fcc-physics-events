<script setup lang="ts">
import { ref, reactive, watch, computed, onMounted, onUnmounted, nextTick } from "vue";
import { watchDebounced, useInfiniteScroll } from "@vueuse/core";
import { getApiClient } from "../composables/getApiClient";
import type { Event, PaginatedResponse } from "../types/event";
import Metadata from "./Metadata.vue";
import NavigationMenu from "./NavigationMenu.vue";

const props = defineProps<{
    initialFilters: Record<string, string>;
}>();

const userSearchQuery = ref("");
const searchInputRef = ref<HTMLInputElement | null>(null);

const searchState = reactive<{
    isLoading: boolean;
    isLoadingMore: boolean;
    events: Event[];
    error: string | null;
    hasMore: boolean;
}>({
    isLoading: false,
    isLoadingMore: false,
    events: [],
    error: null,
    hasMore: true,
});

const pagination = reactive({
    currentPage: 1,
    pageSize: 20,
    totalEvents: 0,
    totalPages: 0,
    loadedPages: new Set<number>(),
});

const expandedRows = reactive(new Set<number>());
const lastToggleAction = ref<"expand" | "collapse" | null>(null);
const infiniteScrollEnabled = ref(true);

const apiClient = getApiClient();

const urlFilterQuery = computed(() => {
    return Object.entries(props.initialFilters)
        .map(([field, value]) => `${field}:"${value}"`)
        .join(" AND ");
});

const combinedSearchQuery = computed(() => {
    const urlPart = urlFilterQuery.value;
    const userPart = userSearchQuery.value.trim();

    if (urlPart && userPart) {
        return `${urlPart} AND ${userPart}`;
    }
    return urlPart || userPart;
});

const allMetadataExpanded = computed(() => {
    const currentEventIds = searchState.events.map((event: Event) => event.process_id);
    if (currentEventIds.length === 0) return false;
    return currentEventIds.every((id: number) => expandedRows.has(id));
});

const searchPlaceholderText = computed(() => {
    return urlFilterQuery.value ? "Add additional search terms..." : 'e.g., detector:"IDEA" AND metadata.status:"done"';
});

const currentDisplayRange = computed(() => {
    if (infiniteScrollEnabled.value) {
        // In infinite scroll mode, show total loaded vs total available
        const totalDisplayed = searchState.events.length;
        const start = totalDisplayed > 0 ? 1 : 0;
        return {
            start,
            end: totalDisplayed,
            total: pagination.totalEvents,
        };
    } else {
        // In pagination mode, show current page range
        const start = (pagination.currentPage - 1) * pagination.pageSize + 1;
        const end = Math.min(pagination.currentPage * pagination.pageSize, pagination.totalEvents);
        return {
            start: searchState.events.length > 0 ? start : 0,
            end,
            total: pagination.totalEvents,
        };
    }
});

const canLoadMore = computed(() => {
    return searchState.hasMore && infiniteScrollEnabled.value && !searchState.isLoading && !searchState.isLoadingMore;
});

async function performSearch(resetResults = true) {
    // Only search if we have a valid query
    if (!combinedSearchQuery.value.trim()) {
        searchState.events = [];
        pagination.totalEvents = 0;
        pagination.totalPages = 0;
        pagination.loadedPages.clear();
        searchState.hasMore = false;
        return;
    }

    const isInitialLoad = resetResults;

    if (isInitialLoad) {
        searchState.isLoading = true;
        searchState.events = [];
        pagination.loadedPages.clear();
        // Only reset to page 1 if we're doing a fresh search (not pagination)
        if (infiniteScrollEnabled.value) {
            pagination.currentPage = 1;
        }
    } else {
        searchState.isLoadingMore = true;
    }

    searchState.error = null;

    try {
        const pageToLoad = isInitialLoad
            ? infiniteScrollEnabled.value
                ? 1
                : pagination.currentPage
            : pagination.currentPage;
        const offset = (pageToLoad - 1) * pagination.pageSize;

        const response: PaginatedResponse = await apiClient.searchSamples(
            combinedSearchQuery.value,
            pagination.pageSize,
            offset,
        );

        if (isInitialLoad || !infiniteScrollEnabled.value) {
            // Replace results for initial load or pagination mode
            searchState.events = response.items;
            pagination.totalEvents = response.total;
            pagination.totalPages = Math.ceil(response.total / pagination.pageSize);
            pagination.loadedPages.clear();
            pagination.loadedPages.add(pageToLoad);
        } else {
            // Append new results for infinite scroll mode
            searchState.events.push(...response.items);
            pagination.loadedPages.add(pageToLoad);
        }

        // Update pagination state
        pagination.totalEvents = response.total;
        pagination.totalPages = Math.ceil(response.total / pagination.pageSize);

        // Check if there are more pages to load
        searchState.hasMore = pagination.currentPage < pagination.totalPages;
    } catch (err) {
        searchState.error = err instanceof Error ? err.message : "Failed to fetch events.";
        if (isInitialLoad) {
            searchState.events = [];
            pagination.totalEvents = 0;
            pagination.totalPages = 0;
        }
        searchState.hasMore = false;
    } finally {
        if (isInitialLoad) {
            searchState.isLoading = false;
        } else {
            searchState.isLoadingMore = false;
        }
    }
}

async function loadMoreData() {
    if (searchState.isLoadingMore || !canLoadMore.value || !searchState.hasMore) {
        return;
    }

    // Load the next page
    pagination.currentPage += 1;
    await performSearch(false);
}

async function jumpToPage(page: number) {
    if (infiniteScrollEnabled.value) {
        // In infinite scroll mode, disable it temporarily and load all pages up to target
        infiniteScrollEnabled.value = false;

        const targetPage = Math.max(1, Math.min(page, pagination.totalPages));

        if (!pagination.loadedPages.has(targetPage)) {
            searchState.isLoading = true;
            searchState.events = [];
            pagination.loadedPages.clear();

            try {
                const promises = [];
                for (let p = 1; p <= targetPage; p++) {
                    const offset = (p - 1) * pagination.pageSize;
                    promises.push(apiClient.searchSamples(combinedSearchQuery.value, pagination.pageSize, offset));
                }

                const responses = await Promise.all(promises);
                const allItems = responses.flatMap((response) => response.items);

                searchState.events = allItems;

                for (let p = 1; p <= targetPage; p++) {
                    pagination.loadedPages.add(p);
                }
            } catch (err) {
                searchState.error = err instanceof Error ? err.message : "Failed to fetch events.";
            } finally {
                searchState.isLoading = false;
            }
        }

        pagination.currentPage = targetPage;

        setTimeout(() => {
            infiniteScrollEnabled.value = true;
        }, 1000);

        await nextTick();
        const targetIndex = (targetPage - 1) * pagination.pageSize;
        const eventCards = document.querySelectorAll("[data-event-card]");
        if (eventCards[targetIndex]) {
            eventCards[targetIndex].scrollIntoView({ behavior: "smooth", block: "start" });
        }
    } else {
        // In pagination mode, load the specific page
        const targetPage = Math.max(1, Math.min(page, pagination.totalPages));
        pagination.currentPage = targetPage;

        // Load the specific page data
        searchState.isLoading = true;
        searchState.error = null;

        try {
            const offset = (targetPage - 1) * pagination.pageSize;
            const response: PaginatedResponse = await apiClient.searchSamples(
                combinedSearchQuery.value,
                pagination.pageSize,
                offset,
            );

            searchState.events = response.items;
            pagination.totalEvents = response.total;
            pagination.totalPages = Math.ceil(response.total / pagination.pageSize);
            pagination.loadedPages.clear();
            pagination.loadedPages.add(targetPage);

            // Check if there are more pages
            searchState.hasMore = targetPage < pagination.totalPages;
        } catch (err) {
            searchState.error = err instanceof Error ? err.message : "Failed to fetch events.";
            searchState.events = [];
        } finally {
            searchState.isLoading = false;
        }
    }
}

function toggleMode() {
    infiniteScrollEnabled.value = !infiniteScrollEnabled.value;

    if (!infiniteScrollEnabled.value) {
        // Switching to pagination mode - reset to show only first page
        pagination.currentPage = 1;
        performSearch(true);
    }
}

function toggleMetadata(processId: number) {
    if (expandedRows.has(processId)) {
        expandedRows.delete(processId);
    } else {
        expandedRows.add(processId);
    }

    const currentEventIds = searchState.events.map((event: Event) => event.process_id);
    const noneExpanded = currentEventIds.every((id: number) => !expandedRows.has(id));

    if (noneExpanded && lastToggleAction.value === "expand") {
        lastToggleAction.value = "collapse";
    }
}

// Handle row click, but ignore if text is being selected or a button was clicked
function handleRowClick(event: MouseEvent, processId: number) {
    const selection = window.getSelection();
    if (selection && selection.toString().length > 0) {
        return;
    }

    const target = event.target as HTMLElement;
    if (target.closest("button, a, input")) {
        return;
    }

    toggleMetadata(processId);
}

// Toggle metadata for all events on the current page.
function toggleAllMetadata() {
    const currentEventIds: Array<number> = searchState.events.map((event: Event) => event.process_id);
    const allAreExpanded = currentEventIds.length > 0 && currentEventIds.every((id: number) => expandedRows.has(id));

    if (allAreExpanded) {
        currentEventIds.forEach((id) => expandedRows.delete(id));
        lastToggleAction.value = "collapse";
    } else {
        currentEventIds.forEach((id) => expandedRows.add(id));
        lastToggleAction.value = "expand";
    }
}

// Handle page size changes and trigger a new search.
function handlePageSizeChange() {
    pagination.currentPage = 1;
    performSearch(true);
}

// Set up infinite scroll on window/document
useInfiniteScroll(window, loadMoreData, {
    distance: 200, // Trigger when 200px from bottom
    canLoadMore: () => canLoadMore.value,
});

// Watch for changes in the initial URL filters to trigger a new search.
watch(
    () => props.initialFilters,
    () => {
        pagination.currentPage = 1;
        performSearch(true);
    },
    { deep: true },
);

// Always set the results page to first page after search
// Perform search 500ms after user stop typing the query
watchDebounced(
    userSearchQuery,
    () => {
        if (pagination.currentPage !== 1) {
            pagination.currentPage = 1;
        }
        performSearch(true);
    },
    { debounce: 500 },
);

// Watch for page changes when in pagination mode
watch(
    () => pagination.currentPage,
    (newPage, oldPage) => {
        // Only trigger if in pagination mode and the page actually changed
        if (!infiniteScrollEnabled.value && newPage !== oldPage) {
            jumpToPage(newPage);
        }
    },
);

// Perform initial search on mount only if there are URL filters
onMounted(() => {
    if (Object.keys(props.initialFilters).length > 0) {
        performSearch(true);
    }
});
</script>

<template>
    <UContainer class="py-4 sm:py-6 lg:py-8">
        <div class="space-y-6">
            <UCard>
                <template #header>
                    <h1 class="text-3xl font-bold">FCC Physics Events Search</h1>
                </template>

                <!-- Navigation Menu moved here -->
                <NavigationMenu />

                <div class="space-y-4 mt-4">
                    <div class="space-y-2">
                        <label class="block text-sm font-medium text-gray-700">
                            Search Query
                            <span v-if="urlFilterQuery" class="text-xs text-gray-600 ml-1">
                                (Additional filters from navigation applied automatically)
                            </span>
                        </label>
                        <UInput
                            ref="searchInputRef"
                            v-model="userSearchQuery"
                            :placeholder="searchPlaceholderText"
                            size="lg"
                            icon="i-heroicons-magnifying-glass"
                            class="w-full"
                        />
                    </div>

                    <UAlert
                        v-if="searchState.error"
                        color="error"
                        variant="soft"
                        icon="i-heroicons-exclamation-triangle"
                        :title="searchState.error"
                        description="Please check your query syntax and try again."
                        closable
                        @close="searchState.error = null"
                    />
                </div>
            </UCard>

            <UCard v-if="searchState.isLoading">
                <div class="space-y-4">
                    <USkeleton v-for="i in 5" :key="i" class="h-12 w-full" />
                </div>
            </UCard>

            <div v-else-if="searchState.events.length > 0" class="space-y-6">
                <div class="flex justify-between items-center">
                    <div class="flex items-center gap-4">
                        <div class="text-md text-gray-600">
                            Showing
                            <strong>{{ currentDisplayRange.start }}-{{ currentDisplayRange.end }}</strong>
                            of <strong>{{ currentDisplayRange.total }}</strong> results
                            <span v-if="searchState.hasMore" class="text-sm text-gray-500">
                                ({{ pagination.loadedPages.size }} of {{ pagination.totalPages }} pages loaded)
                            </span>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="text-md text-gray-600">Results per page:</span>
                            <UInput
                                v-model.number="pagination.pageSize"
                                type="number"
                                min="1"
                                max="100"
                                size="md"
                                class="w-20"
                                @change="handlePageSizeChange"
                            />
                        </div>
                        <UButton
                            :icon="allMetadataExpanded ? 'i-heroicons-eye-slash' : 'i-heroicons-eye'"
                            color="primary"
                            variant="outline"
                            size="sm"
                            class="cursor-pointer"
                            @click="toggleAllMetadata"
                        >
                            {{ allMetadataExpanded ? "Hide All Metadata" : "Show All Metadata" }}
                        </UButton>
                        <UButton
                            :icon="
                                infiniteScrollEnabled ? 'i-heroicons-arrows-up-down' : 'i-heroicons-document-duplicate'
                            "
                            :color="infiniteScrollEnabled ? 'primary' : 'neutral'"
                            variant="outline"
                            size="sm"
                            @click="toggleMode"
                        >
                            {{ infiniteScrollEnabled ? "Infinite Scroll" : "Pagination" }}
                        </UButton>
                    </div>

                    <!-- Only show pagination in pagination mode -->
                    <div v-if="!infiniteScrollEnabled" class="flex justify-center">
                        <UPagination v-model:page="pagination.currentPage" :total="pagination.totalEvents" />
                    </div>
                </div>

                <div class="space-y-2">
                    <UCard
                        v-for="(event, index) in searchState.events"
                        :key="event.process_id"
                        :data-event-card="index"
                        class="overflow-hidden select-text cursor-pointer"
                        @click="handleRowClick($event, event.process_id)"
                    >
                        <div class="px-4 py-1">
                            <div class="flex items-center justify-between gap-4">
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center">
                                        <div class="w-88 flex-shrink-0">
                                            <h3 class="font-semibold text-base text-gray-900">
                                                <span class="ml-1 text-gray-900">{{ event.name }}</span>
                                            </h3>
                                        </div>

                                        <div class="w-42 flex-shrink-0">
                                            <UBadge
                                                v-if="event.framework_name"
                                                color="success"
                                                variant="subtle"
                                                size="md"
                                            >
                                                <span class="text-green-600">Framework:</span>
                                                <span class="ml-1">{{ event.framework_name }}</span>
                                            </UBadge>
                                        </div>

                                        <div class="w-60 flex-shrink-0">
                                            <UBadge
                                                v-if="event.campaign_name"
                                                color="warning"
                                                variant="subtle"
                                                size="md"
                                            >
                                                <span class="text-amber-600">Campaign:</span>
                                                <span class="ml-1">{{ event.campaign_name }}</span>
                                            </UBadge>
                                        </div>

                                        <div class="w-32 flex-shrink-0">
                                            <UBadge v-if="event.detector_name" color="info" variant="subtle" size="md">
                                                <span class="text-blue-600">Detector:</span>
                                                <span class="ml-1">{{ event.detector_name }}</span>
                                            </UBadge>
                                        </div>

                                        <div class="w-40 flex-shrink-0">
                                            <UBadge
                                                v-if="event.accelerator_name"
                                                color="secondary"
                                                variant="subtle"
                                                size="md"
                                            >
                                                <span class="text-purple-600">Accelerator:</span>
                                                <span class="ml-1">{{ event.accelerator_name }}</span>
                                            </UBadge>
                                        </div>
                                    </div>
                                </div>

                                <UButton
                                    :icon="
                                        expandedRows.has(event.process_id)
                                            ? 'i-heroicons-chevron-up'
                                            : 'i-heroicons-chevron-down'
                                    "
                                    color="primary"
                                    variant="ghost"
                                    size="md"
                                    class="cursor-pointer"
                                    :aria-label="`${
                                        expandedRows.has(event.process_id) ? 'Hide' : 'Show'
                                    } metadata for ${event.name}`"
                                    @click.stop="toggleMetadata(event.process_id)"
                                />
                            </div>
                        </div>

                        <Metadata :event="event" v-if="expandedRows.has(event.process_id)" />
                    </UCard>

                    <!-- Infinite scroll loading animation (only in infinite scroll mode) -->
                    <div v-if="searchState.isLoadingMore && infiniteScrollEnabled" class="flex justify-center py-8">
                        <div class="flex items-center space-x-3">
                            <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500"></div>
                            <span class="text-sm text-gray-600">Loading more results...</span>
                            <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500"></div>
                        </div>
                    </div>

                    <!-- Manual load more button (only in infinite scroll mode when auto-loading is disabled) -->
                    <div
                        v-else-if="searchState.hasMore && infiniteScrollEnabled && !canLoadMore"
                        class="flex justify-center py-6"
                    >
                        <UButton
                            color="primary"
                            variant="outline"
                            size="lg"
                            icon="i-heroicons-chevron-down"
                            :loading="searchState.isLoadingMore"
                            @click="loadMoreData"
                        >
                            Load More Results ({{ pagination.totalEvents - searchState.events.length }} remaining)
                        </UButton>
                    </div>

                    <!-- End of results indicator (only in infinite scroll mode) -->
                    <div
                        v-else-if="!searchState.hasMore && searchState.events.length > 0 && infiniteScrollEnabled"
                        class="flex justify-center py-6"
                    >
                        <div class="text-center">
                            <div class="text-gray-500 text-sm">
                                <UIcon name="i-heroicons-check-circle" class="inline mr-1" />
                                All {{ pagination.totalEvents }} results loaded
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Bottom pagination (only in pagination mode) -->
                <div v-if="!infiniteScrollEnabled" class="flex justify-center pt-4">
                    <UPagination v-model:page="pagination.currentPage" :total="pagination.totalEvents" />
                </div>
            </div>

            <UCard v-else class="text-center py-12">
                <p class="text-lg font-medium">No events found.</p>
                <p class="text-sm text-gray-600">Try adjusting your search query.</p>
            </UCard>
        </div>
    </UContainer>
</template>
