// Auto-imported: ref, shallowRef, shallowReactive, computed, readonly, nextTick
import type { Entity, SearchState, ScrollState, SortState, PaginatedResponse } from "~/types/entity";

/**
 * Entity Search Composable
 * Handles entity search, pagination, sorting, and infinite scroll
 */
export function useEntitySearch() {
    const { searchEntities, getSortingFields, baseUrl } = useApiClient();
    const { getNavigationOrder } = useNavigationConfig();
    const { preloadBadgeColors } = useEntityBadges();
    const searchPreferences = useSearchPreferences();

    // Initialize search preferences
    searchPreferences.initializePreferences();

    // Check API availability
    const apiAvailable = computed(() => !!baseUrl);
    const route = useRoute();

    // Component initialization guard - prevent searches until component is ready
    const isComponentReady = ref(false);

    // Search state
    const userSearchQuery = ref((route.query.q as string) || "");
    const infiniteScrollEnabled = ref(true);
    const activeFilters = ref<Record<string, string>>({});
    let currentRequestController: AbortController | null = null;

    // Entity storage - using shallowRef for large arrays that don't need deep reactivity
    const entities = shallowRef<Entity[]>([]);

    // Search operation state - using shallowReactive for better performance
    const searchState = shallowReactive<SearchState>({
        query: "",
        placeholder: "",
        filters: {},
        isLoading: false,
        isLoadingMore: false,
        error: null,
        hasMore: true,
        isSearching: false,
        searchResults: {},
        lastSearchQuery: "",
    });

    // Loading lock to prevent concurrent requests
    let isLoadingLock = false;

    // Track when initial search has completed and stabilized
    let hasCompletedInitialSearch = false;

    // Track when infinite scroll should be active (delayed after initial search)
    const isInfiniteScrollActive = ref(false);

    // Infinite scroll state management
    const scrollState = shallowReactive<ScrollState>({
        currentPage: 1,
        pageSize: searchPreferences.pageSize.value,
        totalEntities: 0,
        loadedPages: new Set<number>(),
    });

    // Sorting state management
    const sortState = shallowReactive<SortState>({
        field: searchPreferences.sortBy.value,
        order: searchPreferences.sortOrder.value,
        sortBy: searchPreferences.sortBy.value,
        sortOrder: searchPreferences.sortOrder.value,
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
        return urlFilterQuery.value ? "Add additional search terms..." : 'e.g., entity_name="value" AND status="done"';
    });

    const showFilterNote = computed(() => !!urlFilterQuery.value);

    const canCopyLink = computed(() => {
        return !!userSearchQuery.value || Object.keys(activeFilters.value).length > 0;
    });

    const currentDisplayRange = readonly(
        computed(() => {
            const totalDisplayed = entities.value.length;
            const start = totalDisplayed > 0 ? 1 : 0;
            return { start, end: totalDisplayed, total: scrollState.totalEntities };
        }),
    );

    const canLoadMore = computed(() => {
        return (
            searchState.hasMore && !searchState.isLoading && !searchState.isLoadingMore && isInfiniteScrollActive.value
        );
    });

    const sortingFieldOptions = computed(() => {
        return sortState.availableFields.map((field) => ({
            label: formatFieldLabel(field),
            value: field,
        }));
    });

    const showLoadingSkeleton = computed(() => {
        return searchState.isLoading && entities.value.length === 0;
    });

    const shouldShowLoadingIndicatorEntities = computed(() => {
        return searchState.isLoadingMore && canLoadMore.value;
    });

    const shouldShowCompletionMessage = computed(() => {
        return !searchState.hasMore && entities.value.length > 0 && scrollState.totalEntities > 0;
    });

    // Utility function
    const formatFieldLabel = (field: string): string => {
        if (field.startsWith("metadata.")) {
            const metadataKey = field.replace("metadata.", "");
            return `${metadataKey.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}`;
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
        // Guard against searches before component is ready
        if (!isComponentReady.value) {
            return;
        }

        if (!apiAvailable.value) {
            console.warn("API is unavailable, skipping search");
            return;
        }

        if (currentRequestController) {
            currentRequestController.abort();
        }
        currentRequestController = new AbortController();
        const searchQuery = combinedSearchQuery.value.trim();
        const isInitialLoad = resetResults;

        if (isInitialLoad) {
            searchState.isLoading = true;
            entities.value = [];
            scrollState.loadedPages.clear();
            scrollState.currentPage = 1; // Always start from page 1 for new searches
            isInfiniteScrollActive.value = false; // Disable infinite scroll during new search
        } else {
            searchState.isLoadingMore = true;
        }
        searchState.error = null;

        try {
            // For infinite scroll: use currentPage directly
            // For initial load: always start with page 1
            const pageToLoad = isInitialLoad ? 1 : scrollState.currentPage;
            const queryToSend = searchQuery || "*";

            const searchParams = {
                query: queryToSend,
                page: pageToLoad,
                pageSize: scrollState.pageSize,
                sortBy: sortState.sortBy,
                sortOrder: sortState.sortOrder,
                filters: activeFilters.value,
            };

            const response: PaginatedResponse = await searchEntities(searchParams);

            if (currentRequestController?.signal.aborted) return;

            const responseEntities = response.data || response.items || [];

            if (isInitialLoad) {
                // Replace all entities for new search
                entities.value = responseEntities as Entity[];
                scrollState.loadedPages.clear();
                scrollState.loadedPages.add(pageToLoad);
            } else {
                // Safeguard: Don't add entities if we've already loaded this page
                if (scrollState.loadedPages.has(pageToLoad)) {
                    console.warn(`Page ${pageToLoad} already loaded, skipping append`);
                    return;
                }

                // Append new entities for infinite scroll
                entities.value = [...entities.value, ...(responseEntities as Entity[])];
                scrollState.loadedPages.add(pageToLoad);
            }

            scrollState.totalEntities = response.total;
            const totalPages = Math.ceil(response.total / scrollState.pageSize);

            // Check if there are more pages available
            searchState.hasMore = pageToLoad < totalPages;
        } catch (error) {
            if (currentRequestController?.signal.aborted) return;
            console.error("Search failed:", error);
            searchState.error = error instanceof Error ? error.message : "Failed to fetch entities.";
            if (isInitialLoad) {
                entities.value = [];
                scrollState.totalEntities = 0;
            }
            searchState.hasMore = false;
        } finally {
            if (!currentRequestController?.signal.aborted) {
                if (isInitialLoad) {
                    searchState.isLoading = false;
                    hasCompletedInitialSearch = true;
                    // Enable infinite scroll when initial search has results
                    if (entities.value.length > 0) {
                        // Use nextTick to ensure DOM is updated before enabling infinite scroll
                        await nextTick();
                        isInfiniteScrollActive.value = true;
                    }
                } else {
                    searchState.isLoadingMore = false;
                }
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

        // Prevent duplicate calls - only allow if no fields loaded yet AND not currently loading
        if (sortState.availableFields.length > 0 || sortState.isLoading) {
            return;
        }

        try {
            sortState.isLoading = true;
            const response = await getSortingFields();
            sortState.availableFields = response.fields || [];
        } catch (error) {
            console.error("Error fetching sorting fields:", error);
        } finally {
            sortState.isLoading = false;
        }
    }

    /**
     * Execute search with scroll state reset
     */
    const executeSearch = (): void => {
        scrollState.currentPage = 1;
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
        // Check loading lock first
        if (isLoadingLock) {
            return;
        }

        // Prevent loading more data before initial search has been performed
        if (entities.value.length === 0) {
            return;
        }

        // Check if we can load more
        if (searchState.isLoadingMore || !canLoadMore.value || !searchState.hasMore) {
            return;
        }

        // Calculate next page to load
        const nextPage = scrollState.currentPage + 1;

        // Safeguard: Don't load if we've already loaded this page
        if (scrollState.loadedPages.has(nextPage)) {
            console.warn(`Page ${nextPage} already loaded, skipping`);
            return;
        }

        // Set loading lock
        isLoadingLock = true;

        try {
            // Update current page and load
            scrollState.currentPage = nextPage;
            await performSearch(false);
        } finally {
            // Always release the lock
            isLoadingLock = false;
        }
    }

    /**
     * Toggle infinite scroll mode (simplified since we only use infinite scroll now)
     */
    const toggleMode = (): void => {
        scrollState.currentPage = 1;
        performSearch(true);
    };

    /**
     * Toggle sort order between ascending and descending
     */
    const toggleSortOrder = (): void => {
        sortState.sortOrder = sortState.sortOrder === "asc" ? "desc" : "asc";
        // Save to preferences
        searchPreferences.setSortOrder(sortState.sortOrder);
    };

    /**
     * Handle page size change
     */
    const handlePageSizeChange = (): void => {
        scrollState.currentPage = 1;
        performSearch(true);
    };

    /**
     * Update filters
     */
    const updateFilters = (newFilters: Record<string, string>): void => {
        if (JSON.stringify(activeFilters.value) !== JSON.stringify(newFilters)) {
            activeFilters.value = { ...newFilters };
        }
    };

    /**
     * Initialize search with filters (no auto-search)
     * Search triggering is now handled by component watchers
     */
    async function initializeSearch(initialFilters: Record<string, string>): Promise<void> {
        // Only update filters - search will be triggered by component watchers
        if (Object.keys(initialFilters).length > 0) {
            updateFilters(initialFilters);
        }
    }

    /**
     * Update methods for readonly state
     */
    const updateCurrentPage = (page: number): void => {
        scrollState.currentPage = Math.max(1, page);
    };

    const updatePageSize = (size: number): void => {
        scrollState.pageSize = size;
        // Save to preferences
        searchPreferences.setPageSize(size);
    };

    const updateSortBy = (field: string): void => {
        sortState.sortBy = field;
        // Save to preferences
        searchPreferences.setSortBy(field);
    };

    const clearError = (): void => {
        searchState.error = null;
    };

    const updateEntity = (index: number, entity: Entity): void => {
        if (index >= 0 && index < entities.value.length) {
            // Use splice to ensure Vue reactivity is triggered
            entities.value.splice(index, 1, { ...entity });
        }
    };

    /**
     * Cleanup function for removing watchers and controllers
     */
    function cleanup(): void {
        if (currentRequestController) {
            currentRequestController.abort();
            currentRequestController = null;
        }
        isLoadingLock = false;
    }

    // Preload badge colors when navigation order is available
    watchEffect(() => {
        const navigationOrder = getNavigationOrder();
        if (navigationOrder.length > 0) {
            // Warm up badge color cache for better UX
            preloadBadgeColors(navigationOrder);
        }
    });

    // Watch preferences and sync to local state
    watch(
        () => searchPreferences.sortBy.value,
        (newSortBy) => {
            if (sortState.sortBy !== newSortBy) {
                sortState.sortBy = newSortBy;
                sortState.field = newSortBy;
            }
        },
        { immediate: true },
    );

    watch(
        () => searchPreferences.sortOrder.value,
        (newSortOrder) => {
            if (sortState.sortOrder !== newSortOrder) {
                sortState.sortOrder = newSortOrder;
                sortState.order = newSortOrder;
            }
        },
        { immediate: true },
    );

    watch(
        () => searchPreferences.pageSize.value,
        (newPageSize) => {
            if (scrollState.pageSize !== newPageSize) {
                scrollState.pageSize = newPageSize;
            }
        },
        { immediate: true },
    );

    return {
        // State
        userSearchQuery,
        infiniteScrollEnabled,
        activeFilters,
        entities,
        searchState,
        scrollState,
        sortState,
        apiAvailable,
        isComponentReady, // Export this so components can control it
        isInfiniteScrollActive, // Export infinite scroll state

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
        shouldShowLoadingIndicatorEntities,
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
        updateEntity,
        cleanup,
    };
}
