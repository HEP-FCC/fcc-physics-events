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
    initialSearchQuery?: string;
    defaultSortBy?: string;
    defaultSortOrder?: "asc" | "desc";
    defaultPageSize?: number;
}

export function datasetSearch(options: SearchOptions) {
    const apiClient = getApiClient();

    // Configuration with sensible defaults
    const defaultSortBy = options.defaultSortBy || "last_edited_at";
    const defaultSortOrder = options.defaultSortOrder || "asc";

    // Core reactive state
    const userSearchQuery = ref(options.initialSearchQuery || "");
    const isInfiniteScrollMode = ref(true);
    const activeFilters = ref(options.initialFilters);
    const isFilterUpdateInProgress = ref(false);

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

    const isClient = () => typeof window !== "undefined";

    const searchPlaceholderText = computed(() => {
        return urlFilterQuery.value
            ? "Add additional search terms..."
            : 'e.g., detector="IDEA" AND metadata.status="done"';
    });

    const currentDisplayRange = computed(() => {
        if (isInfiniteScrollMode.value) {
            const totalDisplayed = searchState.datasets.length;
            const start = totalDisplayed > 0 ? 1 : 0;
            return { start, end: totalDisplayed, total: pagination.totalDatasets };
        } else {
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

    function updateDatasetInState(updatedDataset: Dataset) {
        const index = searchState.datasets.findIndex((d) => d.dataset_id === updatedDataset.dataset_id);
        if (index !== -1) {
            searchState.datasets[index] = updatedDataset;
        }
    }

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
        if (currentRequestController) {
            currentRequestController.abort();
        }
        currentRequestController = new AbortController();
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

            if (isInitialLoad || !isInfiniteScrollMode.value) {
                searchState.datasets = responseDatasets;
                pagination.loadedPages.clear();
                pagination.loadedPages.add(pageToLoad);
            } else {
                searchState.datasets.push(...responseDatasets);
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
                searchState.datasets = [];
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
            }
        }
    }

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
        () => {
            isFilterUpdateInProgress.value = true;
            pagination.currentPage = 1;
            performSearch(true).finally(() => {
                isFilterUpdateInProgress.value = false;
            });
        },
        { debounce: 200, deep: true, immediate: false },
    );

    async function loadMoreData() {
        if (isFilterUpdateInProgress.value || searchState.isLoadingMore || !canLoadMore.value || !searchState.hasMore) {
            return;
        }
        pagination.currentPage += 1;
        await performSearch(false);
    }

    async function jumpToPage(page: number) {
        pagination.currentPage = Math.max(1, Math.min(page, pagination.totalPages));
        if (!isInfiniteScrollMode.value) {
            await performSearch(true);
        }
    }

    function toggleMode() {
        isInfiniteScrollMode.value = !isInfiniteScrollMode.value;
        pagination.currentPage = 1;
        performSearch(true);
    }

    function toggleSortOrder() {
        sortState.sortOrder = sortState.sortOrder === "asc" ? "desc" : "asc";
    }

    function handlePageSizeChange() {
        pagination.currentPage = 1;
        performSearch(true);
    }

    function generatePermalinkUrl(): string {
        if (!isClient()) return "";
        const currentUrl = new URL(window.location.href);
        const params = new URLSearchParams();

        if (userSearchQuery.value.trim()) params.set("q", userSearchQuery.value.trim());
        if (sortState.sortBy !== defaultSortBy) params.set("sort_by", sortState.sortBy);
        if (sortState.sortOrder !== defaultSortOrder) params.set("sort_order", sortState.sortOrder);

        const baseUrl = `${currentUrl.origin}${currentUrl.pathname}`;
        const queryString = params.toString();
        return queryString ? `${baseUrl}?${queryString}` : baseUrl;
    }

    function updateUrlWithSearchState() {
        if (!isClient()) return;
        const newUrl = generatePermalinkUrl();
        if (newUrl !== window.location.href) {
            window.history.replaceState({}, "", newUrl);
        }
    }

    function updateFilters(newFilters: Record<string, string>) {
        if (JSON.stringify(activeFilters.value) !== JSON.stringify(newFilters)) {
            isFilterUpdateInProgress.value = true;
            activeFilters.value = { ...newFilters };
        }
    }

    if (isClient()) {
        useInfiniteScroll(window, () => loadMoreData(), {
            distance: 200,
            canLoadMore: () => canLoadMore.value,
        });
    }

    function executeSearch() {
        pagination.currentPage = 1;
        performSearch(true);
        updateUrlWithSearchState();
    }

    onMounted(async () => {
        await fetchSortingFields();
        // This is now the single source of truth for triggering the initial search.
        // It runs once after the component is mounted and state is initialized.
        performSearch(true);
    });

    onUnmounted(() => {
        if (currentRequestController) {
            currentRequestController.abort();
        }
    });

    return {
        userSearchQuery,
        infiniteScrollEnabled: isInfiniteScrollMode,
        searchState,
        pagination,
        sortState,
        urlFilterQuery,
        combinedSearchQuery,
        searchPlaceholderText,
        currentDisplayRange,
        canLoadMore,
        sortingFieldOptions,
        performSearch,
        executeSearch,
        loadMoreData,
        jumpToPage,
        toggleMode,
        toggleSortOrder,
        handlePageSizeChange,
        generatePermalinkUrl,
        updateUrlWithSearchState,
        updateFilters,
        updateDatasetInState,
    };
}
