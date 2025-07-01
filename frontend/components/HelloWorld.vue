<script setup lang="ts">
import { ref, reactive, watch, computed, onMounted } from "vue";
import { watchDebounced } from "@vueuse/core";
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
    events: Event[];
    error: string | null;
}>({
    isLoading: false,
    events: [],
    error: null,
});

const pagination = reactive({
    currentPage: 1,
    pageSize: 20,
    totalEvents: 0,
});

const expandedRows = reactive(new Set<number>());
const lastToggleAction = ref<"expand" | "collapse" | null>(null);

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

async function performSearch() {
    // Only search if we have a valid query
    if (!combinedSearchQuery.value.trim()) {
        searchState.events = [];
        pagination.totalEvents = 0;
        return;
    }

    searchState.isLoading = true;
    searchState.error = null;

    try {
        const offset = (pagination.currentPage - 1) * pagination.pageSize;
        const response: PaginatedResponse = await apiClient.searchSamples(
            combinedSearchQuery.value,
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
    performSearch();
}

// Format filter names for display
function formatFilterName(key: string): string {
    const nameMap: Record<string, string> = {
        framework_name: "Framework",
        campaign_name: "Campaign",
        detector: "Detector",
        detector_name: "Detector",
    };
    return nameMap[key] || key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
}

watch(() => pagination.currentPage, performSearch);

// // Watch for changes in the initial URL filters to trigger a new search.
watch(
    () => props.initialFilters,
    () => {
        pagination.currentPage = 1;
        performSearch();
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
        } else {
            performSearch();
        }
    },
    { debounce: 500 },
);

// Perform initial search on mount only if there are URL filters
onMounted(() => {
    if (Object.keys(props.initialFilters).length > 0) {
        performSearch();
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
                            <strong
                                >{{ (pagination.currentPage - 1) * pagination.pageSize + 1 }}-{{
                                    Math.min(pagination.currentPage * pagination.pageSize, pagination.totalEvents)
                                }}</strong
                            >
                            of <strong>{{ pagination.totalEvents }}</strong> results
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
                    </div>
                    <UPagination
                        v-model="pagination.currentPage"
                        :total="pagination.totalEvents"
                        :page-count="pagination.pageSize"
                    />
                </div>

                <div class="space-y-2">
                    <UCard
                        v-for="event in searchState.events"
                        :key="event.process_id"
                        class="overflow-hidden select-text cursor-pointer"
                        @click="handleRowClick($event, event.process_id)"
                    >
                        <div class="px-4 py-1">
                            <div class="flex items-center justify-between gap-4">
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center">
                                        <div class="w-88 flex-shrink-0">
                                            <h3 class="font-semibold text-base text-gray-900">
                                                <span class="text-slate-500">Process:</span>
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
                                            <UBadge
                                                v-if="event.detector_name"
                                                color="neutral"
                                                variant="subtle"
                                                size="md"
                                            >
                                                <span class="text-blue-600">Detector:</span>
                                                <span class="ml-1">{{ event.detector_name }}</span>
                                            </UBadge>
                                        </div>

                                        <div class="w-40 flex-shrink-0">
                                            <UBadge
                                                v-if="event.accelerator_name"
                                                color="neutral"
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
                </div>

                <div class="flex justify-center">
                    <UPagination
                        v-model="pagination.currentPage"
                        :total="pagination.totalEvents"
                        :page-count="pagination.pageSize"
                    />
                </div>
            </div>

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
