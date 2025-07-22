import { ref, shallowRef, shallowReactive, computed, readonly } from "vue";
import type { Dataset, SearchState, PaginationState, SortState, PaginatedResponse } from "~/types/dataset";

/**
 * Search functionality composable
 * Handles dataset search, pagination, sorting, and infinite scroll
 */
export function useDatasetSearch() {
    const { apiClient, apiAvailable } = useApiClient();
    const route = useRoute();

    // Search state
    const userSearchQuery = ref((route.query.q as string) || "");
    const infiniteScrollEnabled = ref(true);
    const activeFilters = ref<Record<string, string>>({});
    const isFilterUpdateInProgress = ref(false);
    let currentRequestController: AbortController | null = null;

    // Dataset storage - using shallowRef for large arrays that don't need deep reactivity
    const datasets = shallowRef<Dataset[]>([]);

    // Search operation state - using shallowReactive for better performance
    const searchState = shallowReactive<SearchState>({
        isLoading: false,
        isLoadingMore: false,
        error: null,
        hasMore: true,
    });

    // Pagination state management
    const pagination = shallowReactive<PaginationState>({
        currentPage: 1,
        pageSize: 20,
        totalDatasets: 0,
        totalPages: 0,
        loadedPages: new Set<number>(),
    });

    // Sorting state management
    const sortState = shallowReactive<SortState>({
        sortBy: "last_edited_at",
        sortOrder: "desc",
        availableFields: [],
        isLoading: false,
    });

    // Computed properties
    const urlFilterQuery = computed(() => {
        return Object.entries(activeFilters.value)
            .map(([field, value]) => {
                const searchField = field.replace("_name", "");
                return `${searchField}="${value}"`;
            })
            .join(" AND ");
    });

    const combinedSearchQuery = computed(() => {
        const urlFilterPart = urlFilterQuery.value;
        const userInputPart = userSearchQuery.value.trim();

        if (urlFilterPart && userInputPart) {
            return `${urlFilterPart} AND ${userInputPart}`;
        }
        return urlFilterPart || userInputPart;
    });

    const searchPlaceholderText = computed(() => {
        return urlFilterQuery.value
            ? "Add additional search terms..."
            : 'e.g., entity_name="value" AND metadata.status="done"';
    });

    const showFilterNote = computed(() => !!urlFilterQuery.value);

    const canCopyLink = computed(() => {
        return !!userSearchQuery.value || Object.keys(activeFilters.value).length > 0;
    });

    const currentDisplayRange = readonly(
        computed(() => {
            if (infiniteScrollEnabled.value) {
                const totalDisplayed = datasets.value.length;
                const start = totalDisplayed > 0 ? 1 : 0;
                return { start, end: totalDisplayed, total: pagination.totalDatasets };
            } else {
                const start = (pagination.currentPage - 1) * pagination.pageSize + 1;
                const end = Math.min(pagination.currentPage * pagination.pageSize, pagination.totalDatasets);
                return {
                    start: datasets.value.length > 0 ? start : 0,
                    end,
                    total: pagination.totalDatasets,
                };
            }
        }),
    );

    const canLoadMore = computed(() => {
        return (
            searchState.hasMore &&
            infiniteScrollEnabled.value &&
            !searchState.isLoading &&
            !searchState.isLoadingMore &&
            !isFilterUpdateInProgress.value
        );
    });

    const sortingFieldOptions = computed(() => {
        return sortState.availableFields.map((field) => ({
            label: formatFieldLabel(field),
            value: field,
        }));
    });

    const showLoadingSkeleton = computed(() => {
        return (searchState.isLoading && datasets.value.length === 0) || isFilterUpdateInProgress.value;
    });

    const shouldShowLoadingIndicatorDatasets = computed(() => {
        return searchState.isLoadingMore && infiniteScrollEnabled.value && canLoadMore.value;
    });

    const shouldShowCompletionMessage = computed(() => {
        return !searchState.hasMore && datasets.value.length > 0 && pagination.totalDatasets > 0;
    });

    // Utility function
    const formatFieldLabel = (field: string): string => {
        if (field.startsWith("metadata.")) {
            const metadataKey = field.replace("metadata.", "");
            return `Metadata: ${metadataKey.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}`;
        }
        return field
            .replace(/_/g, " ")
            .replace(/\b\w/g, (l) => l.toUpperCase())
            .replace(" Name", "");
    };

    /**
     * Main search function with pagination and error handling
     */
    async function performSearch(resetResults = true): Promise<void> {
        if (!apiAvailable.value) {
            console.warn("API is unavailable, skipping search");
            return;
        }

        // If this is not a filter-triggered search and filters are updating,
        // wait a bit to avoid race conditions
        if (isFilterUpdateInProgress.value && resetResults) {
            // Wait for a short moment to allow filter updates to settle
            await new Promise((resolve) => setTimeout(resolve, 50));
        }

        if (currentRequestController) {
            currentRequestController.abort();
        }
        currentRequestController = new AbortController();
        const searchQuery = combinedSearchQuery.value.trim();
        const isInitialLoad = resetResults;

        if (isInitialLoad) {
            searchState.isLoading = true;
            datasets.value = [];
            pagination.loadedPages.clear();
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
            const queryToSend = searchQuery || "*";

            const response: PaginatedResponse = await apiClient.searchDatasets(
                queryToSend,
                pagination.pageSize,
                offset,
                sortState.sortBy,
                sortState.sortOrder,
            );

            if (currentRequestController?.signal.aborted) return;

            const responseDatasets = response.data || response.items || [];

            if (isInitialLoad || !infiniteScrollEnabled.value) {
                datasets.value = responseDatasets;
                pagination.loadedPages.clear();
                pagination.loadedPages.add(pageToLoad);
            } else {
                // Create a new array to ensure reactivity triggers
                datasets.value = [...datasets.value, ...responseDatasets];
                pagination.loadedPages.add(pageToLoad);
            }

            pagination.totalDatasets = response.total;
            pagination.totalPages = Math.ceil(response.total / pagination.pageSize);
            searchState.hasMore = pagination.currentPage < pagination.totalPages;
        } catch (error) {
            if (currentRequestController?.signal.aborted) return;
            console.error("Search failed:", error);
            searchState.error = error instanceof Error ? error.message : "Failed to fetch datasets.";
            if (isInitialLoad) {
                datasets.value = [];
                pagination.totalDatasets = 0;
                pagination.totalPages = 0;
            }
            searchState.hasMore = false;
        } finally {
            if (!currentRequestController?.signal.aborted) {
                if (isInitialLoad) {
                    searchState.isLoading = false;
                } else {
                    searchState.isLoadingMore = false;
                }
                // Reset filter update progress flag
                isFilterUpdateInProgress.value = false;
            }
        }
    }

    /**
     * Fetch available sorting fields from API
     */
    async function fetchSortingFields(): Promise<void> {
        if (!apiAvailable.value) {
            console.warn("API is unavailable, skipping sorting fields fetch");
            return;
        }

        // Prevent duplicate calls - only allow if no fields loaded yet
        if (sortState.availableFields.length > 0) {
            return;
        }

        try {
            sortState.isLoading = true;
            const response = await apiClient.getSortingFields();
            sortState.availableFields = response.fields;
        } catch (error) {
            console.error("Error fetching sorting fields:", error);
        } finally {
            sortState.isLoading = false;
        }
    }

    /**
     * Execute search with pagination reset
     */
    const executeSearch = (): void => {
        pagination.currentPage = 1;
        performSearch(true);
    };

    /**
     * Handle search button click
     */
    const handleSearch = (): void => {
        executeSearch();
    };

    /**
     * Load more data for infinite scroll
     */
    async function loadMoreData(): Promise<void> {
        // Prevent loading more data if the first page isn't full, which can happen on initial load
        if (pagination.currentPage === 1 && datasets.value.length < pagination.pageSize) {
            return;
        }

        if (isFilterUpdateInProgress.value || searchState.isLoadingMore || !canLoadMore.value || !searchState.hasMore) {
            return;
        }
        pagination.currentPage += 1;
        await performSearch(false);
    }

    /**
     * Toggle between infinite scroll and pagination modes
     */
    const toggleMode = (): void => {
        infiniteScrollEnabled.value = !infiniteScrollEnabled.value;
        pagination.currentPage = 1;
        performSearch(true);
    };

    /**
     * Toggle sort order between ascending and descending
     */
    const toggleSortOrder = (): void => {
        sortState.sortOrder = sortState.sortOrder === "asc" ? "desc" : "asc";
    };

    /**
     * Handle page size change
     */
    const handlePageSizeChange = (): void => {
        pagination.currentPage = 1;
        performSearch(true);
    };

    /**
     * Update filters and trigger search
     */
    const updateFilters = (newFilters: Record<string, string>): void => {
        if (JSON.stringify(activeFilters.value) !== JSON.stringify(newFilters)) {
            isFilterUpdateInProgress.value = true;
            activeFilters.value = { ...newFilters };
            // Don't trigger immediate search here - let the debounced watcher handle it
        }
    };

    /**
     * Initialize search with auto-search if needed
     */
    async function initializeSearch(initialFilters: Record<string, string>): Promise<void> {
        // Initialize filters from props first
        if (Object.keys(initialFilters).length > 0) {
            updateFilters(initialFilters);
            // Wait a moment for filter update to settle before performing search
            await new Promise((resolve) => setTimeout(resolve, 100));
        }

        // Check conditions for auto-search
        const hasUserQuery = userSearchQuery.value && userSearchQuery.value.trim() !== "";
        const hasActiveFilters = Object.keys(activeFilters.value).length > 0;
        const hasInitialFilters = Object.keys(initialFilters).length > 0;

        // Automatically perform search if query or filters are present, OR if no conditions are met (show all)
        if (hasUserQuery || hasActiveFilters || hasInitialFilters) {
            await performSearch(true);
        } else {
            await performSearch(true);
        }
    }

    /**
     * Update methods for readonly state
     */
    const updateCurrentPage = (page: number): void => {
        pagination.currentPage = Math.max(1, Math.min(page, pagination.totalPages));
    };

    const updatePageSize = (size: number): void => {
        pagination.pageSize = size;
    };

    const updateSortBy = (field: string): void => {
        sortState.sortBy = field;
    };

    const clearError = (): void => {
        searchState.error = null;
    };

    const updateDataset = (index: number, dataset: Dataset): void => {
        if (index >= 0 && index < datasets.value.length) {
            datasets.value[index] = { ...dataset };
        }
    };

    /**
     * Cleanup function
     */
    const cleanup = (): void => {
        if (currentRequestController) {
            currentRequestController.abort();
        }
    };

    return {
        // State
        userSearchQuery,
        infiniteScrollEnabled,
        activeFilters,
        isFilterUpdateInProgress,
        datasets,
        searchState,
        pagination,
        sortState,
        apiAvailable,

        // Computed
        urlFilterQuery,
        combinedSearchQuery,
        searchPlaceholderText,
        showFilterNote,
        canCopyLink,
        currentDisplayRange,
        canLoadMore,
        sortingFieldOptions,
        showLoadingSkeleton,
        shouldShowLoadingIndicatorDatasets,
        shouldShowCompletionMessage,

        // Methods
        performSearch,
        fetchSortingFields,
        executeSearch,
        handleSearch,
        loadMoreData,
        toggleMode,
        toggleSortOrder,
        handlePageSizeChange,
        updateFilters,
        initializeSearch,
        updateCurrentPage,
        updatePageSize,
        updateSortBy,
        clearError,
        updateDataset,
        cleanup,
    };
}
