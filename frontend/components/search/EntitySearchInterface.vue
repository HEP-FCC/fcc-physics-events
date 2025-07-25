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
        <UCard v-if="search.showLoadingSkeleton.value">
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
    console.log("handleRefreshEntity called for entity:", entityId);
    try {
        // Fetch the updated entity from the backend
        const updatedEntity = await getEntityById(entityId);
        console.log("Fetched updated entity:", updatedEntity);
        console.log("Updated entity metadata:", updatedEntity.metadata);

        // Find and update the entity in the current entities array
        const entityIndex = search.entities.value.findIndex((entity: Entity) => {
            return entity.dataset_id === entityId;
        });

        console.log("Entity index in array:", entityIndex);

        if (entityIndex !== -1) {
            console.log("Current entity before update:", search.entities.value[entityIndex]);
            console.log("Updating entity at index", entityIndex, "with:", updatedEntity);
            search.updateEntity(entityIndex, updatedEntity);

            // Force reactivity by waiting for next tick
            await nextTick();
            console.log("Entity after update:", search.entities.value[entityIndex]);
            console.log("Entity updated successfully");
        } else {
            console.warn("Entity not found in current entities array");
        }
    } catch (error) {
        console.error("Failed to refresh entity:", error);
    }
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
