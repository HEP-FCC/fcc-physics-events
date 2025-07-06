import { ref, reactive, computed, watch, onMounted, onUnmounted } from "vue";
import { watchDebounced, useInfiniteScroll } from "@vueuse/core";
import { getApiClient } from "./getApiClient";
import type { Dataset, PaginatedResponse } from "~/types/dataset";

export interface SearchState {
    isLoading: boolean;
    isLoadingMore: boolean;
    datasets: Dataset[];
    error: string | null;
    hasMore: boolean;
}

export interface PaginationState {
    currentPage: number;
    pageSize: number;
    totalDatasets: number;
    totalPages: number;
    loadedPages: Set<number>;
}

export interface SortState {
    sortBy: string;
    sortOrder: "asc" | "desc";
    availableFields: string[];
    isLoading: boolean;
}

export interface SearchOptions {
    initialFilters: Record<string, string>;
    defaultSortBy?: string;
    defaultSortOrder?: "asc" | "desc";
    defaultPageSize?: number;
}

export function useDatasetSearch(options: SearchOptions) {
    const apiClient = getApiClient();

    // Configuration with sensible defaults
    const defaultSortBy = options.defaultSortBy || "last_edited_at";
    const defaultSortOrder = options.defaultSortOrder || "asc";

    // Core reactive state
    const userSearchQuery = ref("");
    const isInfiniteScrollMode = ref(true);
    const activeFilters = ref(options.initialFilters);
    const hasPerformedInitialSearch = ref(false);

    // Abort controller for preventing race conditions between API requests
    let currentRequestController: AbortController | null = null;

    // Search state
    const searchState = reactive<SearchState>({
        isLoading: false,
        isLoadingMore: false,
        datasets: [],
        error: null,
        hasMore: true,
    });

    // Pagination state
    const pagination = reactive<PaginationState>({
        currentPage: 1,
        pageSize: options.defaultPageSize || 20,
        totalDatasets: 0,
        totalPages: 0,
        loadedPages: new Set<number>(),
    });

    // Sort state
    const sortState = reactive<SortState>({
        sortBy: defaultSortBy,
        sortOrder: defaultSortOrder,
        availableFields: [],
        isLoading: false,
    });

    // Computed values for search query building
    const urlFilterQuery = computed(() => {
        return Object.entries(activeFilters.value)
            .map(([field, value]) => {
                // Convert filter field names to search field names (e.g., stage_name -> stage)
                const searchField = field.replace("_name", "");
                return `${searchField}:"${value}"`;
            })
            .join(" AND ");
    });

    // Combined search query (URL filters + user input) for API requests
    const combinedSearchQuery = computed(() => {
        const urlFilterPart = urlFilterQuery.value;
        const userInputPart = userSearchQuery.value.trim();

        if (urlFilterPart && userInputPart) {
            return `${urlFilterPart} AND ${userInputPart}`;
        }
        return urlFilterPart || userInputPart;
    });

    // Helper to check if running on client side
    const isClient = () => typeof window !== "undefined";

    // Search placeholder text based on active filters
    const searchPlaceholderText = computed(() => {
        return urlFilterQuery.value
            ? "Add additional search terms..."
            : 'e.g., detector:"IDEA" AND metadata.status:"done"';
    });

    // Display range for pagination/infinite scroll
    const currentDisplayRange = computed(() => {
        if (isInfiniteScrollMode.value) {
            // Infinite scroll: show loaded vs total available
            const totalDisplayed = searchState.datasets.length;
            const start = totalDisplayed > 0 ? 1 : 0;
            return { start, end: totalDisplayed, total: pagination.totalDatasets };
        } else {
            // Pagination: show current page range
            const start = (pagination.currentPage - 1) * pagination.pageSize + 1;
            const end = Math.min(pagination.currentPage * pagination.pageSize, pagination.totalDatasets);
            return {
                start: searchState.datasets.length > 0 ? start : 0,
                end,
                total: pagination.totalDatasets,
            };
        }
    });

    // Check if more data can be loaded in infinite scroll mode
    const canLoadMore = computed(() => {
        return (
            searchState.hasMore &&
            isInfiniteScrollMode.value &&
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

    // Transform sort field names into user-friendly labels
    function formatFieldLabel(field: string): string {
        if (field.startsWith("metadata.")) {
            const metadataKey = field.replace("metadata.", "");
            return `Metadata: ${metadataKey.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}`;
        }

        return field
            .replace(/_/g, " ")
            .replace(/\b\w/g, (l) => l.toUpperCase())
            .replace(" Name", "");
    }

    // API functions
    async function fetchSortingFields() {
        try {
            sortState.isLoading = true;
            const response = await apiClient.getSortingFields();
            sortState.availableFields = response.fields;
        } catch (error) {
            console.error("Failed to fetch sorting fields:", error);
        } finally {
            sortState.isLoading = false;
        }
    }

    async function performSearch(resetResults = true) {
        // Cancel any ongoing request
        if (currentRequestController) {
            currentRequestController.abort();
        }

        // Create new abort controller
        currentRequestController = new AbortController();

        // Get the search query
        const searchQuery = combinedSearchQuery.value.trim();

        const isInitialLoad = resetResults;

        if (isInitialLoad) {
            searchState.isLoading = true;
            searchState.datasets = [];
            pagination.loadedPages.clear();
            if (isInfiniteScrollMode.value) {
                pagination.currentPage = 1;
            }
        } else {
            searchState.isLoadingMore = true;
        }

        searchState.error = null;

        try {
            const pageToLoad = isInitialLoad
                ? isInfiniteScrollMode.value
                    ? 1
                    : pagination.currentPage
                : pagination.currentPage;
            const offset = (pageToLoad - 1) * pagination.pageSize;

            // Use wildcard for empty queries to get all results
            const queryToSend = searchQuery || "*";

            const response: PaginatedResponse = await apiClient.searchDatasets(
                queryToSend,
                pagination.pageSize,
                offset,
                sortState.sortBy,
                sortState.sortOrder,
            );

            // Check if request was aborted
            if (currentRequestController?.signal.aborted) {
                return;
            }

            // Extract dataset items from response (handle both 'data' and 'items' properties)
            const responseDatasets = response.data || response.items || [];

            if (isInitialLoad || !isInfiniteScrollMode.value) {
                // Replace results for initial load or pagination mode
                searchState.datasets = responseDatasets;
                pagination.loadedPages.clear();
                pagination.loadedPages.add(pageToLoad);
            } else {
                // Append new results for infinite scroll mode
                searchState.datasets.push(...responseDatasets);
                pagination.loadedPages.add(pageToLoad);
            }

            // Update pagination state
            pagination.totalDatasets = response.total;
            pagination.totalPages = Math.ceil(response.total / pagination.pageSize);

            // Check if there are more pages to load
            searchState.hasMore = pagination.currentPage < pagination.totalPages;
        } catch (error) {
            // Don't show error if request was aborted
            if (currentRequestController?.signal.aborted) {
                return;
            }

            console.error("Search failed:", error);
            searchState.error = error instanceof Error ? error.message : "Failed to fetch datasets.";
            if (isInitialLoad) {
                searchState.datasets = [];
                pagination.totalDatasets = 0;
                pagination.totalPages = 0;
            }
            searchState.hasMore = false;
        } finally {
            // Only update loading state if request wasn't aborted
            if (!currentRequestController?.signal.aborted) {
                if (isInitialLoad) {
                    searchState.isLoading = false;
                } else {
                    searchState.isLoadingMore = false;
                }
            }
        }
    }

    // Track filter changes to prevent conflicting operations
    const isFilterUpdateInProgress = ref(false);

    // Watchers
    watch(
        () => pagination.currentPage,
        (newPage, oldPage) => {
            if (!isInfiniteScrollMode.value && newPage !== oldPage) {
                jumpToPage(newPage);
            }
        },
    );

    watch([() => sortState.sortBy, () => sortState.sortOrder], () => {
        pagination.currentPage = 1;
        performSearch(true);
        updateUrlWithSearchState();
    });

    watchDebounced(
        activeFilters,
        (_newFilters) => {
            isFilterUpdateInProgress.value = true;
            pagination.currentPage = 1;
            hasPerformedInitialSearch.value = true;
            performSearch(true).finally(() => {
                isFilterUpdateInProgress.value = false;
            });
        },
        { debounce: 200, deep: true, immediate: false },
    );

    async function loadMoreData() {
        if (isFilterUpdateInProgress.value) {
            return;
        }

        if (searchState.isLoadingMore || !canLoadMore.value || !searchState.hasMore) {
            return;
        }

        pagination.currentPage += 1;
        await performSearch(false);
    }

    async function jumpToPage(page: number) {
        const targetPage = Math.max(1, Math.min(page, pagination.totalPages));
        pagination.currentPage = targetPage;

        if (!isInfiniteScrollMode.value) {
            // In pagination mode, load the specific page
            await performSearch(true);
        }
    }

    function toggleMode() {
        isInfiniteScrollMode.value = !isInfiniteScrollMode.value;

        if (!isInfiniteScrollMode.value) {
            // Switching to pagination mode - reset to show only first page
            pagination.currentPage = 1;
            performSearch(true);
        }
    }

    function toggleSortOrder() {
        sortState.sortOrder = sortState.sortOrder === "asc" ? "desc" : "asc";
    }

    function handlePageSizeChange() {
        pagination.currentPage = 1;
        performSearch(true);
    }

    // URL state management functions
    function generatePermalinkUrl(): string {
        if (!isClient()) {
            return "";
        }

        const currentUrl = new URL(window.location.href);
        const params = new URLSearchParams();

        // Add search query if present
        if (userSearchQuery.value.trim()) {
            params.set("q", userSearchQuery.value.trim());
        }

        // Add sorting parameters if not defaults
        if (sortState.sortBy !== defaultSortBy) {
            params.set("sort_by", sortState.sortBy);
        }
        if (sortState.sortOrder !== defaultSortOrder) {
            params.set("sort_order", sortState.sortOrder);
        }

        // Construct the URL with current path (dropdown filters) and query parameters
        const baseUrl = `${currentUrl.origin}${currentUrl.pathname}`;
        const queryString = params.toString();

        return queryString ? `${baseUrl}?${queryString}` : baseUrl;
    }

    function updateUrlWithSearchState() {
        if (!isClient()) {
            return;
        }

        const newUrl = generatePermalinkUrl();
        const currentUrl = window.location.href;

        if (newUrl !== currentUrl) {
            window.history.replaceState({}, "", newUrl);
        }
    }

    function updateFilters(newFilters: Record<string, string>) {
        // Only update if filters have actually changed
        const filtersChanged = JSON.stringify(activeFilters.value) !== JSON.stringify(newFilters);
        if (filtersChanged) {
            isFilterUpdateInProgress.value = true;
            activeFilters.value = { ...newFilters };
        }
    }

    function loadSearchStateFromUrl() {
        if (!isClient()) {
            return;
        }

        const urlParams = new URLSearchParams(window.location.search);

        // Load search query
        const queryParam = urlParams.get("q");
        if (queryParam) {
            userSearchQuery.value = queryParam;
        }

        // Load sorting parameters
        const sortByParam = urlParams.get("sort_by");
        if (sortByParam) {
            sortState.sortBy = sortByParam;
        }

        const sortOrderParam = urlParams.get("sort_order");
        if (sortOrderParam && (sortOrderParam === "asc" || sortOrderParam === "desc")) {
            sortState.sortOrder = sortOrderParam;
        }
    }

    // Set up infinite scroll (only on client side)
    if (isClient()) {
        useInfiniteScroll(
            window,
            () => {
                loadMoreData();
            },
            {
                distance: 200,
                canLoadMore: () => canLoadMore.value,
            },
        );
    }

    // Manual search function for explicit search triggers
    function executeSearch() {
        isFilterUpdateInProgress.value = true;
        if (pagination.currentPage !== 1) {
            pagination.currentPage = 1;
        }
        performSearch(true).finally(() => {
            isFilterUpdateInProgress.value = false;
        });
        // Update URL only when search is explicitly executed
        updateUrlWithSearchState();
    }

    // Initialize
    onMounted(async () => {
        await fetchSortingFields();
        loadSearchStateFromUrl();

        // Perform initial search only if no filters are set (to avoid double search when filters are passed from props)
        setTimeout(() => {
            if (!hasPerformedInitialSearch.value) {
                const hasInitialFilters = Object.keys(activeFilters.value).length > 0;
                if (!hasInitialFilters) {
                    hasPerformedInitialSearch.value = true;
                    performSearch(true);
                }
            }
        }, 50);
    });

    // Cleanup
    onUnmounted(() => {
        if (currentRequestController) {
            currentRequestController.abort();
        }
    });

    return {
        // State
        userSearchQuery,
        infiniteScrollEnabled: isInfiniteScrollMode,
        searchState,
        pagination,
        sortState,

        // Computed
        urlFilterQuery,
        combinedSearchQuery,
        searchPlaceholderText,
        currentDisplayRange,
        canLoadMore,
        sortingFieldOptions,

        // Methods
        performSearch,
        executeSearch,
        loadMoreData,
        jumpToPage,
        toggleMode,
        toggleSortOrder,
        handlePageSizeChange,
        generatePermalinkUrl,
        updateUrlWithSearchState,
        loadSearchStateFromUrl,
        updateFilters,
    };
}
