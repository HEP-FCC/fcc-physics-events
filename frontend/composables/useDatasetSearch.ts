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

    // Store defaults for consistent use
    const defaultSortBy = options.defaultSortBy || "last_edited_at";
    const defaultSortOrder = options.defaultSortOrder || "asc";

    // Core state
    const userSearchQuery = ref("");
    const infiniteScrollEnabled = ref(true);

    // Make initialFilters reactive by converting to ref
    const currentFilters = ref(options.initialFilters);

    // Add abort controller for request cancellation
    let currentAbortController: AbortController | null = null;

    // Track if initial search has been performed
    const hasPerformedInitialSearch = ref(false);

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
            .map(([field, value]) => {
                // Convert filter field names to search field names
                // e.g., stage_name -> stage, campaign_name -> campaign, detector_name -> detector
                const searchField = field.replace("_name", "");
                return `${searchField}:"${value}"`;
            })
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
        const result =
            searchState.hasMore &&
            infiniteScrollEnabled.value &&
            !searchState.isLoading &&
            !searchState.isLoadingMore &&
            !filterChangeInProgress.value;
        console.log(
            `🔄 canLoadMore computed - hasMore: ${searchState.hasMore}, infiniteScroll: ${infiniteScrollEnabled.value}, isLoading: ${searchState.isLoading}, isLoadingMore: ${searchState.isLoadingMore}, filterChange: ${filterChangeInProgress.value}, result: ${result}`,
        );
        return result;
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
        // Cancel any ongoing request
        if (currentAbortController) {
            currentAbortController.abort();
        }

        // Create new abort controller
        currentAbortController = new AbortController();

        // Get the search query
        const searchQuery = combinedSearchQuery.value.trim();

        const isInitialLoad = resetResults;

        console.log(
            `🔍 Performing search - Query: "${searchQuery}" | Filters: ${JSON.stringify(
                currentFilters.value,
            )} | Reset: ${resetResults}`,
        );
        console.log(
            `📊 Current pagination state - Page: ${pagination.currentPage}, PageSize: ${pagination.pageSize}, InfiniteScroll: ${infiniteScrollEnabled.value}`,
        );

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
            console.log(`🔎 Final query to send: "${queryToSend}"`);
            console.log(`📊 Pagination params - Page: ${pageToLoad}, Offset: ${offset}, Limit: ${pagination.pageSize}`);

            const response: PaginatedResponse = await apiClient.searchDatasets(
                queryToSend,
                pagination.pageSize,
                offset,
                sortState.sortBy,
                sortState.sortOrder,
            );

            // Check if request was aborted
            if (currentAbortController?.signal.aborted) {
                console.log("🚫 Search request was aborted");
                return;
            }

            console.log(`✅ Search completed: ${response.items?.length || 0} results | Total: ${response.total}`);
            console.log(`📋 Full response structure:`, response);
            console.log(`📋 Response.items:`, response.items);

            // Check if the response has data instead of items
            const responseItems = (response as any).data || response.items || [];
            console.log(`📋 Actual items array:`, responseItems, `Length: ${responseItems.length}`);

            if (isInitialLoad || !infiniteScrollEnabled.value) {
                // Replace results for initial load or pagination mode
                searchState.datasets = responseItems;
                pagination.totalDatasets = response.total;
                pagination.totalPages = Math.ceil(response.total / pagination.pageSize);
                pagination.loadedPages.clear();
                pagination.loadedPages.add(pageToLoad);
            } else {
                // Append new results for infinite scroll mode
                searchState.datasets.push(...responseItems);
                pagination.loadedPages.add(pageToLoad);
            }

            // Update pagination state
            pagination.totalDatasets = response.total;
            pagination.totalPages = Math.ceil(response.total / pagination.pageSize);

            // Check if there are more pages to load
            searchState.hasMore = pagination.currentPage < pagination.totalPages;
        } catch (err) {
            // Don't show error if request was aborted
            if (currentAbortController?.signal.aborted) {
                console.log("🚫 Search request was aborted (error handler)");
                return;
            }

            console.error("❌ Search failed:", err);
            searchState.error = err instanceof Error ? err.message : "Failed to fetch datasets.";
            if (isInitialLoad) {
                searchState.datasets = [];
                pagination.totalDatasets = 0;
                pagination.totalPages = 0;
            }
            searchState.hasMore = false;
        } finally {
            // Only update loading state if request wasn't aborted
            if (!currentAbortController?.signal.aborted) {
                if (isInitialLoad) {
                    searchState.isLoading = false;
                } else {
                    searchState.isLoadingMore = false;
                }
            }
        }
    }

    let filterChangeInProgress = ref(false);

    // Watchers
    watch(
        () => pagination.currentPage,
        (newPage, oldPage) => {
            console.log(
                `📄 Page watcher triggered - New: ${newPage}, Old: ${oldPage}, InfiniteScroll: ${infiniteScrollEnabled.value}`,
            );
            if (!infiniteScrollEnabled.value && newPage !== oldPage) {
                console.log(`📄 Calling jumpToPage(${newPage})`);
                jumpToPage(newPage);
            }
        },
    );

    watch([() => sortState.sortBy, () => sortState.sortOrder], () => {
        pagination.currentPage = 1;
        performSearch(true);
        updateUrlWithSearchState();
    });

    // Use debounced watcher for filters to prevent rapid successive searches
    watchDebounced(
        currentFilters,
        (newFilters) => {
            console.log(`⏰ Filter watcher triggered - Filters: ${JSON.stringify(newFilters)}`);
            filterChangeInProgress.value = true;
            console.log("🚩 Filter watcher: Filter change in progress, flag set.");
            pagination.currentPage = 1;
            hasPerformedInitialSearch.value = true;
            performSearch(true).finally(() => {
                filterChangeInProgress.value = false;
                console.log("✅ Filter change search complete, flag reset.");
            });
        },
        { debounce: 200, deep: true, immediate: false },
    );

    async function loadMoreData() {
        console.log(`📈 loadMoreData called - filterChange: ${filterChangeInProgress.value}`);
        if (filterChangeInProgress.value) {
            console.log("🚫 loadMoreData call skipped: filter change in progress.");
            return;
        }
        console.log(
            `📈 loadMoreData proceeding - isLoadingMore: ${searchState.isLoadingMore}, canLoadMore: ${canLoadMore.value}, hasMore: ${searchState.hasMore}`,
        );
        if (searchState.isLoadingMore || !canLoadMore.value || !searchState.hasMore) {
            console.log("🚫 loadMoreData blocked by conditions");
            return;
        }

        pagination.currentPage += 1;
        console.log(`📈 loadMoreData calling performSearch(false) - Page: ${pagination.currentPage}`);
        await performSearch(false);
    }

    async function jumpToPage(page: number) {
        console.log(`🦘 jumpToPage called with page: ${page}, current totalPages: ${pagination.totalPages}`);
        const targetPage = Math.max(1, Math.min(page, pagination.totalPages));
        pagination.currentPage = targetPage;

        if (!infiniteScrollEnabled.value) {
            console.log(`🦘 jumpToPage calling performSearch(true) - Page: ${targetPage}`);
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
        // Check if we're on the client side
        if (typeof window === "undefined") {
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
        // Check if we're on the client side
        if (typeof window === "undefined") {
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
        const filtersChanged = JSON.stringify(currentFilters.value) !== JSON.stringify(newFilters);
        console.log(
            `🔄 updateFilters called - Changed: ${filtersChanged} | Old: ${JSON.stringify(
                currentFilters.value,
            )} | New: ${JSON.stringify(newFilters)}`,
        );
        if (filtersChanged) {
            filterChangeInProgress.value = true;
            console.log("🚩 Filter change in progress, flag set.");
            currentFilters.value = { ...newFilters };
        }
    }

    function loadSearchStateFromUrl() {
        // Check if we're on the client side
        if (typeof window === "undefined") {
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
    if (typeof window !== "undefined") {
        console.log("🔄 Setting up infinite scroll");
        useInfiniteScroll(
            window,
            () => {
                console.log("🌊 Infinite scroll triggered!");
                loadMoreData();
            },
            {
                distance: 200,
                canLoadMore: () => {
                    const canLoad = canLoadMore.value;
                    console.log(`🌊 Infinite scroll canLoadMore check: ${canLoad}`);
                    return canLoad;
                },
            },
        );
    }

    // Manual search function for explicit search triggers
    function executeSearch() {
        filterChangeInProgress.value = true;
        console.log("🚩 executeSearch: Filter change in progress, flag set.");
        if (pagination.currentPage !== 1) {
            pagination.currentPage = 1;
        }
        performSearch(true).finally(() => {
            filterChangeInProgress.value = false;
            console.log("✅ executeSearch: Search complete, flag reset.");
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
                const hasInitialFilters = Object.keys(currentFilters.value).length > 0;
                if (!hasInitialFilters) {
                    hasPerformedInitialSearch.value = true;
                    performSearch(true);
                }
            }
        }, 50);
    });

    // Cleanup
    onUnmounted(() => {
        if (currentAbortController) {
            currentAbortController.abort();
        }
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
