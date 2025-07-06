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
        <UCard v-if="shouldShowLoadingSkeleton">
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

// Initialize search functionality with default configuration
const search = useDatasetSearch({
    initialFilters: props.initialFilters,
    defaultSortBy: "last_edited_at",
    defaultSortOrder: "desc",
    defaultPageSize: 20,
});

// Initialize dataset selection/metadata expansion functionality
const selection = useDatasetSelection();

// API client for backend communication
const apiClient = getApiClient();

// Track loading skeleton visibility with delay to prevent flashing
const isLoadingSkeletonVisible = ref(false);
let loadingTimeout: NodeJS.Timeout | null = null;

// Watch loading state with delay to prevent flash on quick responses
watch(
    () => search.searchState.isLoading,
    (isLoading) => {
        if (isLoading) {
            // Show loading skeleton after 300ms delay
            loadingTimeout = setTimeout(() => {
                isLoadingSkeletonVisible.value = true;
            }, 300);
        } else {
            // Immediately hide loading and clear any pending timeout
            if (loadingTimeout) {
                clearTimeout(loadingTimeout);
                loadingTimeout = null;
            }
            isLoadingSkeletonVisible.value = false;
        }
    },
    { immediate: true },
);

// Determine when to show loading skeleton
const shouldShowLoadingSkeleton = computed(() => {
    return search.searchState.isLoading && (isLoadingSkeletonVisible.value || search.searchState.datasets.length === 0);
});

// Generate download filename with timestamp
function generateDownloadFilename(datasetCount: number): string {
    const now = new Date();
    const timestamp = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(
        now.getDate(),
    ).padStart(2, "0")}_${String(now.getHours()).padStart(2, "0")}-${String(now.getMinutes()).padStart(
        2,
        "0",
    )}-${String(now.getSeconds()).padStart(2, "0")}`;

    return `fcc_physics_datasets-${datasetCount}-datasets-${timestamp}.json`;
}

// Download data as JSON file
function downloadJsonFile(data: unknown, filename: string): void {
    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

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
            const filename = generateDownloadFilename(datasetsToDownload.length);
            downloadJsonFile(datasetsToDownload, filename);
        }
    } catch (error) {
        console.error("Failed to download datasets:", error);
        alert("An error occurred while downloading the datasets. Please try again.");
    } finally {
        selection.selectionState.isDownloading = false;
    }
}

// Event handlers
function handleSearch() {
    search.executeSearch();
}

function handleRowClick(_event: MouseEvent, datasetId: number) {
    selection.toggleMetadata(datasetId);
}

function handlePermalinkCopied() {
    // Toast notification could be added here if desired
}

// Handle filter changes from navigation
watchDebounced(
    () => props.initialFilters,
    (newFilters, oldFilters) => {
        // On first load, oldFilters will be undefined
        const isInitialLoad = oldFilters === undefined;
        const filtersChanged = JSON.stringify(newFilters) !== JSON.stringify(oldFilters);

        if (isInitialLoad || filtersChanged) {
            search.updateFilters(newFilters);

            // Force search on initial load if filters are present
            if (isInitialLoad && Object.keys(newFilters).length > 0) {
                search.executeSearch();
            }

            // Clear metadata expansions when navigation changes
            selection.clearMetadataExpansions();
        }
    },
    { debounce: 50, deep: true, immediate: true },
);

// Clear metadata expansions when search results or pagination changes
watch(
    () => search.searchState.datasets,
    () => {
        selection.clearMetadataExpansions();
    },
);

watch(
    () => search.pagination.currentPage,
    () => {
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
