<template>
    <div class="space-y-6">
        <!-- Search Header Card -->
        <UCard>
            <template #header>
                <h1 class="text-3xl font-bold">FCC Physics Datasets Search</h1>
            </template>

            <!-- Navigation Menu -->
            <NavigationMenu />

            <div class="space-y-4 mt-4">
                <!-- Search Controls -->
                <SearchControls
                    v-model="search.userSearchQuery.value"
                    :placeholder="search.searchPlaceholderText.value"
                    :show-filter-note="!!search.urlFilterQuery"
                    :can-copy-link="!!search.userSearchQuery || Object.keys(props.initialFilters).length > 0"
                    :generate-permalink-url="search.generatePermalinkUrl"
                    @search="handleSearch"
                    @permalink-copied="handlePermalinkCopied"
                />

                <!-- Error Alert -->
                <UAlert
                    v-if="search.searchState.error"
                    color="error"
                    variant="soft"
                    icon="i-heroicons-exclamation-triangle"
                    :title="search.searchState.error"
                    description="Please check your query syntax and try again."
                    closable
                    @close="search.searchState.error = null"
                />
            </div>
        </UCard>

        <!-- Loading State -->
        <UCard v-if="showLoadingSkeleton">
            <div class="space-y-4">
                <USkeleton v-for="i in 5" :key="i" class="h-12 w-full" />
            </div>
        </UCard>

        <!-- Results -->
        <div v-else-if="search.searchState.datasets.length > 0" class="space-y-6">
            <!-- Main controls header -->
            <div
                class="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800"
            >
                <!-- Left side: Actions & View Options -->
                <DatasetControls
                    :all-selected="selection.allDatasetsSelected.value(search.searchState.datasets)"
                    :selected-count="selection.selectedCount.value"
                    :total-datasets="search.searchState.datasets.length"
                    :is-downloading="selection.selectionState.isDownloading"
                    :all-metadata-expanded="selection.allMetadataExpanded.value(search.searchState.datasets)"
                    :sort-by="search.sortState.sortBy"
                    :sort-order="search.sortState.sortOrder"
                    :sorting-options="search.sortingFieldOptions.value"
                    :sorting-loading="search.sortState.isLoading"
                    :infinite-scroll-enabled="search.infiniteScrollEnabled.value"
                    @toggle-select-all="selection.toggleSelectAll(search.searchState.datasets)"
                    @download-selected="downloadSelectedDatasets"
                    @toggle-all-metadata="selection.toggleAllMetadata(search.searchState.datasets)"
                    @update:sort-by="search.sortState.sortBy = $event"
                    @toggle-sort-order="search.toggleSortOrder"
                    @toggle-mode="search.toggleMode"
                />

                <!-- Right side: Pagination & Results Info -->
                <ResultsSummary
                    :display-range="search.currentDisplayRange.value"
                    :page-size="search.pagination.pageSize"
                    :infinite-scroll-enabled="search.infiniteScrollEnabled.value"
                    :current-page="search.pagination.currentPage"
                    :total-datasets="search.pagination.totalDatasets"
                    @update:page-size="search.pagination.pageSize = $event"
                    @page-size-changed="search.handlePageSizeChange"
                    @update:page="search.pagination.currentPage = $event"
                />
            </div>

            <!-- Dataset List -->
            <DatasetList
                :datasets="search.searchState.datasets"
                :is-loading-more="search.searchState.isLoadingMore"
                :has-more="search.searchState.hasMore"
                :infinite-scroll-enabled="search.infiniteScrollEnabled.value"
                :can-auto-load="search.canLoadMore.value"
                :total-datasets="search.pagination.totalDatasets"
                :remaining-results="search.pagination.totalDatasets - search.searchState.datasets.length"
                :is-dataset-selected="selection.isDatasetSelected"
                :is-metadata-expanded="selection.isMetadataExpanded"
                @toggle-selection="selection.toggleDatasetSelection"
                @toggle-metadata="selection.toggleMetadata"
                @row-click="handleRowClick"
                @load-more="search.loadMoreData"
            />

            <!-- Bottom pagination (only in pagination mode) -->
            <div v-if="!search.infiniteScrollEnabled.value" class="flex justify-center pt-4">
                <UPagination
                    :page="search.pagination.currentPage"
                    :total="search.pagination.totalPages"
                    @update:page="search.pagination.currentPage = $event"
                />
            </div>
        </div>

        <!-- No Results -->
        <UCard v-else class="text-center py-12 text-gray-600 dark:text-gray-400">
            <p class="text-lg font-medium">No datasets found.</p>
            <p class="text-sm">Try adjusting your search query. 🔎</p>
        </UCard>
    </div>
</template>

<script setup lang="ts">
import { watch, computed } from "vue";
import { watchDebounced } from "@vueuse/core";
import { getApiClient } from "~/composables/getApiClient";
import { useDatasetSearch } from "~/composables/useDatasetSearch";
import { useDatasetSelection } from "~/composables/useDatasetSelection";
import { useLoadingDelay } from "~/composables/useLoadingDelay";
import { useDatasetDownload } from "~/composables/useDatasetDownload";
import type { DatasetSearchInterfaceProps } from "~/types/components";

const props = defineProps<DatasetSearchInterfaceProps>();

// Initialize search functionality with optimized defaults
const search = useDatasetSearch({
    initialFilters: props.initialFilters,
    defaultSortBy: "last_edited_at",
    defaultSortOrder: "desc",
    defaultPageSize: 20,
});

// Initialize dataset selection and metadata expansion functionality
const selection = useDatasetSelection();

const apiClient = getApiClient();

// Initialize download functionality
const downloadUtils = useDatasetDownload();

// Use simplified loading delay utility
const loadingState = useLoadingDelay({ delayMs: 300 });

// Show loading skeleton when search is loading and either delay has passed or no data exists
const showLoadingSkeleton = computed(() => {
    return (
        search.searchState.isLoading &&
        (loadingState.shouldShowLoading.value || search.searchState.datasets.length === 0)
    );
});

// Watch search loading state to manage loading delay
watch(
    () => search.searchState.isLoading,
    (isLoading) => {
        if (isLoading) {
            loadingState.startLoading();
        } else {
            loadingState.stopLoading();
        }
    },
    { immediate: true },
);

// Handle dataset download using the utility
async function downloadSelectedDatasets() {
    const selectedDatasetIds = Array.from(selection.selectionState.selectedDatasets);

    if (selectedDatasetIds.length === 0) {
        // Could show a toast notification here instead of alert
        return;
    }

    const success = await downloadUtils.downloadSelectedDatasets(selectedDatasetIds, apiClient, (isLoading) => {
        selection.selectionState.isDownloading = isLoading;
    });

    // Optional: Show success/error feedback to user
    // if (!success) {
    //     // Show error toast notification
    // }
}

// Event handlers
function handleSearch() {
    search.executeSearch();
}

function handleRowClick(_event: MouseEvent, datasetId: number) {
    selection.toggleMetadata(datasetId);
}

function handlePermalinkCopied() {
    // Could add toast notification here if desired
}

// Handle filter changes from navigation
watchDebounced(
    () => props.initialFilters,
    (newFilters, oldFilters) => {
        const isInitialLoad = oldFilters === undefined;
        const filtersChanged = JSON.stringify(newFilters) !== JSON.stringify(oldFilters);

        if (isInitialLoad || filtersChanged) {
            search.updateFilters(newFilters);

            // Execute search on initial load if filters are present
            if (isInitialLoad && Object.keys(newFilters).length > 0) {
                search.executeSearch();
            }

            selection.clearMetadataExpansions();
        }
    },
    { debounce: 50, deep: true, immediate: true },
);

// Clear metadata expansions when search results or pagination changes
watch(
    () => search.searchState.datasets,
    () => selection.clearMetadataExpansions(),
);
watch(
    () => search.pagination.currentPage,
    () => selection.clearMetadataExpansions(),
);
</script>
