<template>
    <div class="entity-search-interface space-y-6">
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
        <UCard v-if="search.showLoadingSkeleton.value || !isInitialized">
            <div class="space-y-4">
                <USkeleton v-for="i in 5" :key="i" class="h-12 w-full" />
            </div>
        </UCard>

        <!-- Results -->
        <div v-else-if="search.entities.value.length > 0" class="space-y-6">
            <!-- Entity Controls & Results Summary -->
            <EntityControls
                :entities="search.entities.value as Entity[]"
                :all-entities-selected="allEntitiesSelected"
                :selected-count="selection.selectedCount.value"
                :is-downloading="selection.selectionState.isDownloading"
                :is-downloading-filtered="selection.isDownloadingFiltered.value"
                :all-metadata-expanded="allMetadataExpanded"
                :sort-by="search.sortState.sortBy"
                :sort-order="search.sortState.sortOrder"
                :sorting-field-options="search.sortingFieldOptions.value"
                :sort-loading="search.sortState.isLoading"
                :display-range="search.currentDisplayRange.value"
                :page-size="search.scrollState.pageSize"
                @toggle-select-all="selection.toggleSelectAll(search.entities.value as Entity[])"
                @download-selected="selection.downloadSelectedEntities"
                @download-filtered="
                    selection.downloadAllFilteredEntities({
                        query: search.combinedSearchQuery.value,
                        sortBy: search.sortState.sortBy,
                        sortOrder: search.sortState.sortOrder,
                    })
                "
                @toggle-all-metadata="selection.toggleAllMetadata(search.entities.value as Entity[])"
                @update-sort-by="search.updateSortBy"
                @toggle-sort-order="search.toggleSortOrder"
                @update-page-size="search.updatePageSize"
                @handle-page-size-change="search.handlePageSizeChange"
            />

            <!-- Entity List -->
            <EntityList
                :entities="search.entities.value as Entity[]"
                :scroll-state="search.scrollState"
                :sort-state="search.sortState"
                :selection-state="selection.selectionState"
                :search-state="search.searchState"
                :metadata-edit-state="selection.metadataEditState"
                :infinite-scroll-enabled="search.infiniteScrollEnabled.value"
                :sorting-field-options="search.sortingFieldOptions.value"
                :current-display-range="search.currentDisplayRange.value"
                :should-show-loading-indicator="search.shouldShowLoadingIndicatorEntities.value"
                :should-show-completion-message="search.shouldShowCompletionMessage.value"
                :active-filters="search.activeFilters.value"
                @toggle-entity-selection="selection.toggleEntitySelection"
                @toggle-metadata="selection.toggleMetadata"
                @enter-edit-mode="selection.enterEditMode"
                @cancel-edit="selection.cancelEdit"
                @save-metadata="
                    (entityId: number, editedJson?: string) =>
                        selection.saveMetadataChanges(
                            entityId,
                            search.entities.value as Entity[],
                            search.updateEntity,
                            editedJson,
                        )
                "
                @refresh-entity="handleRefreshEntity"
            />

            <!-- Loading States -->
            <div v-if="search.shouldShowLoadingIndicatorEntities.value" class="flex justify-center py-8">
                <div class="flex items-center space-x-3 text-sm text-gray-600 dark:text-gray-400">
                    <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500" />
                    <span>Loading more results...</span>
                </div>
            </div>

            <div v-else-if="search.shouldShowCompletionMessage.value" class="flex justify-center py-6">
                <div class="text-center text-sm text-gray-500 dark:text-gray-400">
                    <UIcon name="i-heroicons-check-circle" class="inline mr-1" />
                    All {{ search.scrollState.totalEntities }} {{ mainTableDisplayName.toLowerCase() }} loaded
                </div>
            </div>
        </div>

        <!-- No Results -->
        <UCard v-else class="text-center py-12 text-gray-600 dark:text-gray-400">
            <p class="text-lg font-medium">No {{ mainTableDisplayName }} found.</p>
            <p class="text-sm">Try adjusting your search query or filters. 🔎</p>
        </UCard>
    </div>
</template>

<script setup lang="ts">
// Auto-imported: ref, computed, onMounted, onUnmounted, watch, watchEffect
// Auto-imported: watchDebounced, useInfiniteScroll
// Auto-imported: nextTick
import type { Entity } from "~/types/entity";
// Auto-imported: useDynamicNavigation
// Auto-imported: extractEntityIds
// Auto-imported: useAppConfiguration
import SearchControls from "./SearchControls.vue";
import EntityControls from "../entities/EntityControls.vue";
import EntityList from "../entities/EntityList.vue";

/**
 * Entity Search Interface Component
 * Main interface for searching and managing entities
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
const search = useEntitySearch();
const selection = useEntitySelection();
const { mainTableDisplayName } = useAppConfiguration();

// Component state
const isInitialized = ref(false);

// Reactive state for duplicate search prevention
const lastSearchKey = ref<string>("");

// Computed current path from route params (for watcher consistency)
const currentPath = computed(() => {
    try {
        return parseRouteToPath(props.routeParams);
    } catch (error) {
        console.error("Error parsing route to path:", error);
        return {};
    }
});

// Memoized selection state computations
const allEntitiesSelected = computed(() => selection.getAllEntitiesSelected(search.entities.value as Entity[]));
const allMetadataExpanded = computed(() => selection.getAllMetadataExpanded(search.entities.value as Entity[]));

/**
 * Handle click outside dropdown - now handled by NavigationMenu
 */
const handleClickOutside = (_event: Event): void => {
    // Navigation dropdowns are now handled by NavigationMenu itself
};

// Handle entity refresh after lock state changes
const { getEntityById } = useApiClient();
const handleRefreshEntity = async (entityId: number): Promise<void> => {
    try {
        // Fetch the updated entity from the backend
        const updatedEntity = await getEntityById(entityId);

        // Find and update the entity in the current entities array
        const entityIndex = search.entities.value.findIndex((entity: Entity) => {
            return entity.dataset_id === entityId;
        });

        if (entityIndex !== -1) {
            search.updateEntity(entityIndex, updatedEntity);

            // Force reactivity by waiting for next tick
            await nextTick();
        } else {
            console.warn("Entity not found in current entities array");
        }
    } catch (error) {
        console.error("Failed to refresh entity:", error);
    }
};

// Watchers
// Use watchDebounced to prevent multiple rapid fires
watchDebounced(
    [isInitialized, () => JSON.stringify(props.initialFilters), () => props.routeParams.length],
    ([initialized, filtersStr, routeParamsLength]) => {
        const filters = JSON.parse(filtersStr);

        // Only proceed if component is initialized
        if (!initialized) {
            return;
        }

        // Skip if filters are empty but we have route params (waiting for filters to populate)
        const hasRouteParams = routeParamsLength > 0;
        const hasFilters = Object.keys(filters).length > 0;

        if (hasRouteParams && !hasFilters) {
            return;
        }

        // Create a search key to prevent duplicate searches with same parameters
        const searchKey = JSON.stringify({
            filters,
            searchQuery: search.userSearchQuery.value,
            routeParamsLength,
        });

        // Skip if this exact search was already performed
        if (searchKey === lastSearchKey.value) {
            return;
        }

        lastSearchKey.value = searchKey;

        // Update filters - use the already parsed filters from props
        search.updateFilters(filters);

        // Perform search (navigation dropdowns are prioritized separately in NavigationMenu)
        search.performSearch(true);
    },
    { debounce: 300, immediate: false, flush: "post" },
);

// Watch sorting changes to trigger new search
watch(
    [() => search.sortState.sortBy, () => search.sortState.sortOrder],
    () => {
        // Only trigger search if component is fully initialized
        if (isInitialized.value) {
            search.updateCurrentPage(1);
            search.performSearch(true);
        }
    },
    { flush: "post" },
);

// Clear metadata expansions when entities change (only when entity IDs change)
watch(
    () => extractEntityIds(search.entities.value),
    () => selection.clearMetadataExpansions(),
    { flush: "post" },
);

// Clear metadata expansions when page changes
watch(
    () => search.scrollState.currentPage,
    () => selection.clearMetadataExpansions(),
    { flush: "post" },
);

// Set up infinite scroll - but only after component is ready
useInfiniteScroll(
    window,
    () => {
        // Guard against infinite scroll triggers before component is ready
        if (search.isComponentReady.value) {
            search.loadMoreData();
        }
    },
    {
        distance: 600,
        canLoadMore: () => search.canLoadMore.value && search.isComponentReady.value,
    },
);

// Component lifecycle
onMounted(async () => {
    if (!isInitialized.value) {
        const { initializeNavigation } = useDynamicNavigation();

        try {
            // Priority 1: Initialize navigation configuration first (for immediate UI feedback)
            // This enables dropdown loading and ensures navigation is ready before other operations
            await initializeNavigation();

            // Priority 2: Fetch sorting fields in background (non-blocking for search)
            // Start this but don't wait for it - it can complete asynchronously
            search.fetchSortingFields().catch((error) => {
                console.error("Background sorting fields loading failed:", error);
            });
        } catch (error) {
            console.error("Error during navigation initialization:", error);
        }

        // Mark component as ready for searches (this will trigger the watcher for entity search)
        search.isComponentReady.value = true;

        // Mark component as initialized (this will trigger the main search watcher)
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
