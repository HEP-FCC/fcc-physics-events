import { ref, reactive, computed, watch, onMounted } from "vue";
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

    // Store defaults for consistent use
    const defaultSortBy = options.defaultSortBy || "last_edited_at";
    const defaultSortOrder = options.defaultSortOrder || "asc";

    // Core state
    const userSearchQuery = ref("");
    const infiniteScrollEnabled = ref(true);

    // Make initialFilters reactive by converting to ref
    const currentFilters = ref(options.initialFilters);

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

    // Computed properties
    const urlFilterQuery = computed(() => {
        return Object.entries(currentFilters.value)
            .map(([field, value]) => `${field}:"${value}"`)
            .join(" AND ");
    });

    const combinedSearchQuery = computed(() => {
        const urlPart = urlFilterQuery.value;
        const userPart = userSearchQuery.value.trim();

        if (urlPart && userPart) {
            return `${urlPart} AND ${userPart}`;
        }
        return urlPart || userPart;
    });

    const searchPlaceholderText = computed(() => {
        return urlFilterQuery.value
            ? "Add additional search terms..."
            : 'e.g., detector:"IDEA" AND metadata.status:"done"';
    });

    const currentDisplayRange = computed(() => {
        if (infiniteScrollEnabled.value) {
            // In infinite scroll mode, show total loaded vs total available
            const totalDisplayed = searchState.datasets.length;
            const start = totalDisplayed > 0 ? 1 : 0;
            return {
                start,
                end: totalDisplayed,
                total: pagination.totalDatasets,
            };
        } else {
            // In pagination mode, show current page range
            const start = (pagination.currentPage - 1) * pagination.pageSize + 1;
            const end = Math.min(pagination.currentPage * pagination.pageSize, pagination.totalDatasets);
            return {
                start: searchState.datasets.length > 0 ? start : 0,
                end,
                total: pagination.totalDatasets,
            };
        }
    });

    const canLoadMore = computed(() => {
        return (
            searchState.hasMore && infiniteScrollEnabled.value && !searchState.isLoading && !searchState.isLoadingMore
        );
    });

    const sortingFieldOptions = computed(() => {
        return sortState.availableFields.map((field) => ({
            label: formatFieldLabel(field),
            value: field,
        }));
    });

    // Utility functions
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
        // Get the search query
        const searchQuery = combinedSearchQuery.value.trim();

        const isInitialLoad = resetResults;

        if (isInitialLoad) {
            searchState.isLoading = true;
            searchState.datasets = [];
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

            // Use wildcard for empty queries to get all results
            const queryToSend = searchQuery || "*";
            const response: PaginatedResponse = await apiClient.searchDatasets(
                queryToSend,
                pagination.pageSize,
                offset,
                sortState.sortBy,
                sortState.sortOrder,
            );

            if (isInitialLoad || !infiniteScrollEnabled.value) {
                // Replace results for initial load or pagination mode
                searchState.datasets = response.items;
                pagination.totalDatasets = response.total;
                pagination.totalPages = Math.ceil(response.total / pagination.pageSize);
                pagination.loadedPages.clear();
                pagination.loadedPages.add(pageToLoad);
            } else {
                // Append new results for infinite scroll mode
                searchState.datasets.push(...response.items);
                pagination.loadedPages.add(pageToLoad);
            }

            // Update pagination state
            pagination.totalDatasets = response.total;
            pagination.totalPages = Math.ceil(response.total / pagination.pageSize);

            // Check if there are more pages to load
            searchState.hasMore = pagination.currentPage < pagination.totalPages;
        } catch (err) {
            searchState.error = err instanceof Error ? err.message : "Failed to fetch datasets.";
            if (isInitialLoad) {
                searchState.datasets = [];
                pagination.totalDatasets = 0;
                pagination.totalPages = 0;
            }
            searchState.hasMore = false;
        } finally {
            if (isInitialLoad) {
                searchState.isLoading = false;
            } else {
                searchState.isLoadingMore = false;
            }
        }
    }

    async function loadMoreData() {
        if (searchState.isLoadingMore || !canLoadMore.value || !searchState.hasMore) {
            return;
        }

        pagination.currentPage += 1;
        await performSearch(false);
    }

    async function jumpToPage(page: number) {
        const targetPage = Math.max(1, Math.min(page, pagination.totalPages));
        pagination.currentPage = targetPage;

        if (!infiniteScrollEnabled.value) {
            // In pagination mode, load the specific page
            await performSearch(true);
        }
    }

    function toggleMode() {
        infiniteScrollEnabled.value = !infiniteScrollEnabled.value;

        if (!infiniteScrollEnabled.value) {
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

    // URL state management
    function generatePermalinkUrl(): string {
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
        const newUrl = generatePermalinkUrl();
        const currentUrl = window.location.href;

        if (newUrl !== currentUrl) {
            window.history.replaceState({}, "", newUrl);
        }
    }

    function updateFilters(newFilters: Record<string, string>) {
        currentFilters.value = { ...newFilters };
    }

    function loadSearchStateFromUrl() {
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

    // Set up infinite scroll
    useInfiniteScroll(window, loadMoreData, {
        distance: 200,
        canLoadMore: () => canLoadMore.value,
    });

    // Manual search function for explicit search triggers
    function executeSearch() {
        if (pagination.currentPage !== 1) {
            pagination.currentPage = 1;
        }
        performSearch(true);
        // Update URL only when search is explicitly executed
        updateUrlWithSearchState();
    }

    // Watchers
    watch(
        () => pagination.currentPage,
        (newPage, oldPage) => {
            if (!infiniteScrollEnabled.value && newPage !== oldPage) {
                jumpToPage(newPage);
            }
        },
    );

    watch([() => sortState.sortBy, () => sortState.sortOrder], () => {
        pagination.currentPage = 1;
        performSearch(true);
        updateUrlWithSearchState();
    });


    // Watch for changes in filters and trigger search (but not on initial mount)
    watch(
        currentFilters,
        () => {
            pagination.currentPage = 1;
            performSearch(true);
        },
        { deep: true, immediate: false },
    );

    // Initialize
    onMounted(async () => {
        await fetchSortingFields();
        loadSearchStateFromUrl();

        // Always perform initial search - this ensures we show data even with no filters
        performSearch(true);
    });

    return {
        // State
        userSearchQuery,
        infiniteScrollEnabled,
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
