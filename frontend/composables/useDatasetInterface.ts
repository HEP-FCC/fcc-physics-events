import { computed } from "vue";
import { useDatasetSearch } from "./useDatasetSearch";
import { useDatasetSelection } from "./useDatasetSelection";
import type { Dataset } from "~/types/dataset";

interface UseDatasetInterfaceOptions {
    initialFilters: Record<string, string>;
    defaultSortBy?: string;
    defaultSortOrder?: "asc" | "desc";
    defaultPageSize?: number;
}

export function useDatasetInterface(options: UseDatasetInterfaceOptions) {
    // Initialize composables
    const search = useDatasetSearch({
        initialFilters: options.initialFilters,
        defaultSortBy: options.defaultSortBy || "last_edited_at",
        defaultSortOrder: options.defaultSortOrder || "desc",
        defaultPageSize: options.defaultPageSize || 20,
    });

    const selection = useDatasetSelection();

    // Computed helpers for common operations
    const resultsState = computed(() => ({
        hasResults: search.searchState.datasets.length > 0,
        isLoading: search.searchState.isLoading,
        hasError: !!search.searchState.error,
        canDownload: selection.selectedCount.value > 0,
        displayRange: search.currentDisplayRange,
    }));

    // Helper functions that combine both composables
    const actions = {
        // Selection actions
        toggleDatasetSelection: selection.toggleDatasetSelection,
        toggleSelectAll: (datasets: Dataset[]) => selection.toggleSelectAll(datasets),
        toggleMetadata: selection.toggleMetadata,
        toggleAllMetadata: (datasets: Dataset[]) => selection.toggleAllMetadata(datasets),

        // Search actions
        performSearch: search.performSearch,
        loadMoreData: search.loadMoreData,
        toggleMode: search.toggleMode,
        toggleSortOrder: search.toggleSortOrder,
        handlePageSizeChange: search.handlePageSizeChange,
        updateFilters: search.updateFilters,

        // Combined actions
        handleRowClick: (_event: MouseEvent, datasetId: number) => {
            selection.toggleMetadata(datasetId);
        },

        generatePermalinkUrl: search.generatePermalinkUrl,
    };

    return {
        // Grouped state for cleaner access
        search: {
            state: search.searchState,
            pagination: search.pagination,
            sort: search.sortState,
            query: search.userSearchQuery,
            filters: search.urlFilterQuery,
            combined: search.combinedSearchQuery,
            placeholder: search.searchPlaceholderText,
            infiniteScroll: search.infiniteScrollEnabled,
            canLoadMore: search.canLoadMore,
            sortOptions: search.sortingFieldOptions,
        },

        selection: {
            state: selection.selectionState,
            count: selection.selectedCount,
            allSelected: selection.allDatasetsSelected,
            allExpanded: selection.allMetadataExpanded,
            isSelected: selection.isDatasetSelected,
            isExpanded: selection.isMetadataExpanded,
        },

        // Results state helpers
        resultsState,

        // Actions
        actions,

        // Legacy compatibility - expose original references for gradual migration
        userSearchQuery: search.userSearchQuery,
        infiniteScrollEnabled: search.infiniteScrollEnabled,
        searchState: search.searchState,
        pagination: search.pagination,
        sortState: search.sortState,
        urlFilterQuery: search.urlFilterQuery,
        combinedSearchQuery: search.combinedSearchQuery,
        searchPlaceholderText: search.searchPlaceholderText,
        currentDisplayRange: search.currentDisplayRange,
        canLoadMore: search.canLoadMore,
        sortingFieldOptions: search.sortingFieldOptions,
        performSearch: search.performSearch,
        loadMoreData: search.loadMoreData,
        toggleMode: search.toggleMode,
        toggleSortOrder: search.toggleSortOrder,
        handlePageSizeChange: search.handlePageSizeChange,
        generatePermalinkUrl: search.generatePermalinkUrl,
        updateFilters: search.updateFilters,
        selectionState: selection.selectionState,
        selectedCount: selection.selectedCount,
        allDatasetsSelected: selection.allDatasetsSelected,
        allMetadataExpanded: selection.allMetadataExpanded,
        toggleDatasetSelection: selection.toggleDatasetSelection,
        toggleSelectAll: selection.toggleSelectAll,
        toggleMetadata: selection.toggleMetadata,
        toggleAllMetadata: selection.toggleAllMetadata,
        isDatasetSelected: selection.isDatasetSelected,
        isMetadataExpanded: selection.isMetadataExpanded,
    };
}
