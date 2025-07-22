<template>
    <div class="dataset-search-interface space-y-6">
        <!-- Navigation -->
        <NavigationMenu :route-params="props.routeParams" />

        <!-- Search Controls -->
        <SearchControls
            :key="`search-controls-stable`"
            v-model:search-query="search.userSearchQuery.value"
            :search-placeholder-text="search.searchPlaceholderText.value"
            :show-filter-note="search.showFilterNote.value"
            :can-copy-link="search.canCopyLink.value"
            :search-error="search.searchState.error"
            :api-available="search.apiAvailable.value"
            @search="search.handleSearch"
            @clear-error="search.clearError"
        />

        <!-- Loading Skeleton -->
        <UCard v-if="search.showLoadingSkeleton.value">
            <div class="space-y-4">
                <USkeleton v-for="i in 5" :key="i" class="h-12 w-full" />
            </div>
        </UCard>

        <!-- Results -->
        <div v-else-if="search.datasets.value.length > 0" class="space-y-6">
            <!-- Dataset Controls & Results Summary -->
            <DatasetControls
                :datasets="search.datasets.value as Dataset[]"
                :all-entities-selected="allEntitiesSelected"
                :selected-count="selection.selectedCount.value"
                :is-downloading="selection.selectionState.isDownloading"
                :all-metadata-expanded="allMetadataExpanded"
                :sort-by="search.sortState.sortBy"
                :sort-order="search.sortState.sortOrder"
                :sorting-field-options="search.sortingFieldOptions.value"
                :sort-loading="search.sortState.isLoading"
                :display-range="search.currentDisplayRange.value"
                :page-size="search.pagination.pageSize"
                @toggle-select-all="selection.toggleSelectAll(search.datasets.value as Dataset[])"
                @download-selected="selection.downloadSelectedEntities"
                @toggle-all-metadata="selection.toggleAllMetadata(search.datasets.value as Dataset[])"
                @update-sort-by="search.updateSortBy"
                @toggle-sort-order="search.toggleSortOrder"
                @update-page-size="search.updatePageSize"
                @handle-page-size-change="search.handlePageSizeChange"
            />

            <!-- Dataset List -->
            <DatasetList
                :datasets="search.datasets.value as Dataset[]"
                :pagination="search.pagination"
                :sort-state="search.sortState"
                :selection-state="selection.selectionState"
                :search-state="search.searchState"
                :metadata-edit-state="selection.metadataEditState"
                :infinite-scroll-enabled="search.infiniteScrollEnabled.value"
                :sorting-field-options="search.sortingFieldOptions.value"
                :current-display-range="search.currentDisplayRange.value"
                :should-show-loading-indicator="search.shouldShowLoadingIndicatorDatasets.value"
                :should-show-completion-message="search.shouldShowCompletionMessage.value"
                @toggle-entity-selection="selection.toggleEntitySelection"
                @toggle-metadata="selection.toggleMetadata"
                @enter-edit-mode="selection.enterEditMode"
                @cancel-edit="selection.cancelEdit"
                @save-metadata="
                    (datasetId: number, editedJson?: string) =>
                        selection.saveMetadataChanges(
                            datasetId,
                            search.datasets.value as Dataset[],
                            search.updateDataset,
                            editedJson,
                        )
                "
            />

            <!-- Loading States -->
            <div v-if="search.shouldShowLoadingIndicatorDatasets.value" class="flex justify-center py-8">
                <div class="flex items-center space-x-3 text-sm text-gray-600 dark:text-gray-400">
                    <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500" />
                    <span>Loading more results...</span>
                </div>
            </div>

            <div v-else-if="search.shouldShowCompletionMessage.value" class="flex justify-center py-6">
                <div class="text-center text-sm text-gray-500 dark:text-gray-400">
                    <UIcon name="i-heroicons-check-circle" class="inline mr-1" />
                    All {{ search.pagination.totalDatasets }} results loaded
                </div>
            </div>
        </div>

        <!-- No Results -->
        <UCard v-else class="text-center py-12 text-gray-600 dark:text-gray-400">
            <p class="text-lg font-medium">No datasets found.</p>
            <p class="text-sm">Try adjusting your search query or filters. 🔎</p>
        </UCard>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, watchEffect } from "vue";
import { watchDebounced, useInfiniteScroll } from "@vueuse/core";
import type { Dataset } from "~/types/dataset";
import { useDynamicNavigation } from "~/composables/useDynamicNavigation";
import { extractEntityIds } from "~/composables/useEntityCompat";

/**
 * Dataset Search Interface Component
 * Main interface for searching and managing physics datasets
 */

interface Props {
    initialFilters?: Record<string, string>;
    routeParams?: string[];
}

const props = withDefaults(defineProps<Props>(), {
    initialFilters: () => ({}),
    routeParams: () => [],
});

// Dynamic navigation composable
const { parseRouteToPath } = useDynamicNavigation();

// Composables
const search = useDatasetSearch();
const selection = useEntitySelection();

// Component state
const isInitialized = ref(false);

// Async navigation state
const currentPath = ref<Record<string, string | null>>({});

// Watch route params and update data asynchronously
watchEffect(() => {
    const params = props.routeParams;
    try {
        currentPath.value = parseRouteToPath(params);
    } catch (error) {
        console.error("Error parsing route to path:", error);
        currentPath.value = {};
    }
});

// Memoized selection state computations
const allEntitiesSelected = computed(() => selection.getAllEntitiesSelected(search.datasets.value as Dataset[]));
const allMetadataExpanded = computed(() => selection.getAllMetadataExpanded(search.datasets.value as Dataset[]));

/**
 * Handle click outside dropdown - now handled by NavigationMenu
 */
const handleClickOutside = (_event: Event): void => {
    // Navigation dropdowns are now handled by NavigationMenu itself
};

// Watchers
// Watch for route param changes and update filters
watch(
    currentPath,
    (newPath, _oldPath) => {
        // Build navigation filters from current path
        const navigationFilters = Object.entries(newPath)
            .filter(([, value]) => value !== null)
            .reduce((acc, [key, value]) => {
                acc[`${key}_name`] = value!;
                return acc;
            }, {} as Record<string, string>);

        // Update filters
        search.updateFilters(navigationFilters);

        // Note: Dropdown state management is now handled by NavigationMenu
    },
    { immediate: true, deep: true, flush: "post" },
);

// Watch sorting changes to trigger new search
watch(
    [() => search.sortState.sortBy, () => search.sortState.sortOrder],
    () => {
        search.updateCurrentPage(1);
        search.performSearch(true);
    },
    { flush: "post" },
);

// Watch filter changes with debounce
watchDebounced(
    search.activeFilters,
    () => {
        // Only proceed if not already in a filter update process from elsewhere
        if (!search.isFilterUpdateInProgress.value) {
            search.isFilterUpdateInProgress.value = true;
        }
        search.updateCurrentPage(1);
        search.performSearch(true).finally(() => {
            search.isFilterUpdateInProgress.value = false;
        });
    },
    { debounce: 250, deep: true, immediate: false, flush: "post" },
);

// Clear metadata expansions when datasets change (only when dataset IDs change)
watch(
    () => extractEntityIds(search.datasets.value),
    () => selection.clearMetadataExpansions(),
    { flush: "post" },
);

// Clear metadata expansions when page changes
watch(
    () => search.pagination.currentPage,
    () => selection.clearMetadataExpansions(),
    { flush: "post" },
);

// Set up infinite scroll
useInfiniteScroll(window, () => search.loadMoreData(), {
    distance: 800,
    canLoadMore: () => search.canLoadMore.value,
});

// Component lifecycle
onMounted(async () => {
    if (!isInitialized.value) {
        // Initialize navigation configuration first (needed for badges)
        const { initializeNavigation } = useDynamicNavigation();
        await initializeNavigation();

        // Initialize search with any initial filters
        await search.initializeSearch(props.initialFilters);

        // Fetch sorting fields
        await search.fetchSortingFields();

        // Note: Navigation dropdown data is now loaded by NavigationMenu itself

        isInitialized.value = true;
    }

    // Add click outside handler (now mostly handled by NavigationMenu)
    document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
    // Clean up event listeners
    document.removeEventListener("click", handleClickOutside);

    // Clean up composables
    search.cleanup();
});
</script>
