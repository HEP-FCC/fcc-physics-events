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
        <UCard v-if="shouldShowLoading">
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
                    :total="search.pagination.totalDatasets"
                    :page-count="search.pagination.pageSize"
                    @update:page="search.pagination.currentPage = $event"
                />
            </div>
        </div>

        <!-- No Results -->
        <UCard v-else class="text-center py-12 text-gray-600 dark:text-gray-400">
            <p class="text-lg font-medium">No datasets found.</p>
            <p class="text-sm">Try adjusting your search query.</p>
        </UCard>
    </div>
</template>

<script setup lang="ts">
import { watch, ref, computed, onUnmounted } from "vue";
import { watchDebounced } from "@vueuse/core";
import { getApiClient } from "~/composables/getApiClient";
import { useDatasetSearch } from "~/composables/useDatasetSearch";
import { useDatasetSelection } from "~/composables/useDatasetSelection";
import type { DatasetSearchInterfaceProps } from "~/types/components";

const props = defineProps<DatasetSearchInterfaceProps>();

// Initialize composables with namespace approach
const search = useDatasetSearch({
    initialFilters: props.initialFilters,
    defaultSortBy: "last_edited_at",
    defaultSortOrder: "desc",
    defaultPageSize: 20,
});

const selection = useDatasetSelection();

const apiClient = getApiClient();

// Delayed loading state to prevent flashing
const showLoadingAfterDelay = ref(false);
let loadingTimeout: NodeJS.Timeout | null = null;

// Watch loading state with delay
watch(
    () => search.searchState.isLoading,
    (isLoading) => {
        if (isLoading) {
            // Show loading after 300ms to prevent flash on quick responses
            loadingTimeout = setTimeout(() => {
                showLoadingAfterDelay.value = true;
            }, 300);
        } else {
            // Immediately hide loading and clear timeout
            if (loadingTimeout) {
                clearTimeout(loadingTimeout);
                loadingTimeout = null;
            }
            showLoadingAfterDelay.value = false;
        }
    },
    { immediate: true },
);

// Computed property for whether to show loading skeleton
const shouldShowLoading = computed(() => {
    return search.searchState.isLoading && (showLoadingAfterDelay.value || search.searchState.datasets.length === 0);
});

// Handle dataset download
async function downloadSelectedDatasets() {
    if (selection.selectionState.selectedDatasets.size === 0) {
        alert("Please select at least one dataset to download.");
        return;
    }

    selection.selectionState.isDownloading = true;
    try {
        const datasetsToDownload = await apiClient.downloadDatasetsByIds(
            Array.from(selection.selectionState.selectedDatasets),
        );

        if (datasetsToDownload.length > 0) {
            const jsonStr = JSON.stringify(datasetsToDownload, null, 2);
            const blob = new Blob([jsonStr], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;

            const now = new Date();
            const timestamp = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(
                now.getDate(),
            ).padStart(2, "0")}_${String(now.getHours()).padStart(2, "0")}-${String(now.getMinutes()).padStart(
                2,
                "0",
            )}-${String(now.getSeconds()).padStart(2, "0")}`;
            const numberOfDatasets = datasetsToDownload.length;
            link.download = `fcc_physics_datasets-${numberOfDatasets}-datasets-${timestamp}.json`;

            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }
    } catch (error) {
        console.error("Failed to download datasets:", error);
        alert("An error occurred while downloading the datasets. Please try again.");
    } finally {
        selection.selectionState.isDownloading = false;
    }
}

// Handle manual search trigger
function handleSearch() {
    search.executeSearch();
}

// Handle row click for metadata toggle
function handleRowClick(_event: MouseEvent, datasetId: number) {
    selection.toggleMetadata(datasetId);
}

// Handle permalink copy feedback
function handlePermalinkCopied() {
    // Could add toast notification here if desired
    console.log("Link copied to clipboard");
}

// Watch for changes in initial filters (navigation changes)
watchDebounced(
    () => props.initialFilters,
    (newFilters, oldFilters) => {
        console.log(
            `📡 DatasetSearchInterface filter watcher - Old: ${JSON.stringify(oldFilters)} | New: ${JSON.stringify(
                newFilters,
            )}`,
        );

        // On first load, oldFilters will be undefined, so we need to handle that case
        const isInitialLoad = oldFilters === undefined;
        const filtersChanged = JSON.stringify(newFilters) !== JSON.stringify(oldFilters);

        if (isInitialLoad || filtersChanged) {
            console.log(
                `📡 ${isInitialLoad ? "Initial load" : "Filter change"} - updating filters in search composable`,
            );
            search.updateFilters(newFilters);

            // If it's initial load and we have filters, force a search
            if (isInitialLoad && Object.keys(newFilters).length > 0) {
                console.log(`📡 Initial load with filters detected, forcing search`);
                search.executeSearch();
            }

            // Clear metadata expansions when filters change (e.g., navigation)
            selection.clearMetadataExpansions();
        }
    },
    { debounce: 50, deep: true, immediate: true },
);

// Watch for changes in search results and clear metadata expansions
watch(
    () => search.searchState.datasets,
    () => {
        // Clear metadata expansions when datasets change (search, pagination, etc.)
        selection.clearMetadataExpansions();
    },
);

// Watch for changes in current page and clear metadata expansions
watch(
    () => search.pagination.currentPage,
    () => {
        // Clear metadata expansions when page changes
        selection.clearMetadataExpansions();
    },
);

// Cleanup timeout on unmount
onUnmounted(() => {
    if (loadingTimeout) {
        clearTimeout(loadingTimeout);
    }
});
</script>
