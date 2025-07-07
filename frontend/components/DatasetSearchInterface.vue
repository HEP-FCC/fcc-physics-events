<template>
    <div class="space-y-6">
        <UCard>
            <template #header>
                <h1 class="text-3xl font-bold">FCC Physics Datasets Search</h1>
            </template>

            <NavigationMenu :route-params="props.routeParams" />

            <div class="space-y-4 mt-4">
                <SearchControls
                    v-model="search.userSearchQuery.value"
                    :placeholder="search.searchPlaceholderText.value"
                    :show-filter-note="!!search.urlFilterQuery"
                    :can-copy-link="!!search.userSearchQuery || Object.keys(props.initialFilters).length > 0"
                    :generate-permalink-url="search.generatePermalinkUrl"
                    @search="handleSearch"
                    @permalink-copied="handlePermalinkCopied"
                />

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

        <UCard v-if="showLoadingSkeleton">
            <div class="space-y-4">
                <USkeleton v-for="i in 5" :key="i" class="h-12 w-full" />
            </div>
        </UCard>

        <div v-else-if="search.searchState.datasets.length > 0" class="space-y-6">
            <div
                class="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800"
            >
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

            <div v-if="!search.infiniteScrollEnabled.value" class="flex justify-center pt-4">
                <UPagination
                    :page="search.pagination.currentPage"
                    :total="search.pagination.totalPages"
                    @update:page="search.pagination.currentPage = $event"
                />
            </div>
        </div>

        <UCard v-else class="text-center py-12 text-gray-600 dark:text-gray-400">
            <p class="text-lg font-medium">No datasets found.</p>
            <p class="text-sm">Try adjusting your search query. 🔎</p>
        </UCard>
    </div>
</template>

<script setup lang="ts">
import { watch, computed, nextTick } from "vue";
import { watchDebounced } from "@vueuse/core";
import { getApiClient } from "~/composables/getApiClient";
import { datasetSearch } from "~/composables/datasetSearch";
import { datasetSelection } from "~/composables/datasetSelection";
import { loadingDelay } from "~/composables/loadingDelay";
import { datasetDownload } from "~/composables/datasetDownload";
import type { DatasetSearchInterfaceProps } from "~/types/components";

const props = withDefaults(defineProps<DatasetSearchInterfaceProps>(), {
    routeParams: () => [],
});

const search = datasetSearch({
    initialFilters: props.initialFilters,
    defaultSortBy: "last_edited_at",
    defaultSortOrder: "desc",
    defaultPageSize: 20,
});

const selection = datasetSelection();

const apiClient = getApiClient();

const downloadUtils = datasetDownload();

const loadingState = loadingDelay({ delayMs: 300 });

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
    async (newFilters, oldFilters) => {
        const isInitialLoad = oldFilters === undefined;
        const filtersChanged = JSON.stringify(newFilters) !== JSON.stringify(oldFilters);

        if (isInitialLoad || filtersChanged) {
            // On initial load, ensure URL search state is loaded first
            if (isInitialLoad) {
                search.loadSearchStateFromUrl();
            }

            search.updateFilters(newFilters);

            // Execute search on initial load if filters are present or if there's a URL query
            if (isInitialLoad && (Object.keys(newFilters).length > 0 || search.userSearchQuery.value.trim())) {
                // Small delay to ensure all state is synchronized
                await nextTick();
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
