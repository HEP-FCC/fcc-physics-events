import type { Dataset } from "./dataset";

// Common event handlers
export interface DatasetSelectionEvents {
    "toggle-selection": [datasetId: number];
    "toggle-metadata": [datasetId: number];
    "row-click": [event: MouseEvent, datasetId: number];
}

export interface DatasetControlEvents {
    "toggle-select-all": [];
    "download-selected": [];
    "toggle-all-metadata": [];
    "update:sort-by": [value: string];
    "toggle-sort-order": [];
    "toggle-mode": [];
}

export interface SearchEvents {
    "permalink-copied": [];
    search: [];
}

export interface PaginationEvents {
    "update:page-size": [value: number];
    "page-size-changed": [];
    "update:page": [value: number];
    "load-more": [];
}

// Common props patterns
export interface SelectionProps {
    isDatasetSelected: (id: number) => boolean;
    isMetadataExpanded: (id: number) => boolean;
}

export interface SortingProps {
    sortBy: string;
    sortOrder: "asc" | "desc";
    sortingOptions: SortOption[];
    sortingLoading: boolean;
}

export interface PaginationProps {
    infiniteScrollEnabled: boolean;
    hasMore: boolean;
    isLoadingMore: boolean;
    canAutoLoad: boolean;
    totalDatasets: number;
    remainingResults: number;
}

// Specific component interfaces
export interface DatasetCardProps {
    dataset: Dataset;
    index: number;
    isSelected: boolean;
    isExpanded: boolean;
}

export interface DatasetListProps extends SelectionProps, PaginationProps {
    datasets: Dataset[];
}

export interface DatasetControlsProps extends SortingProps {
    allSelected: boolean;
    selectedCount: number;
    totalDatasets: number;
    isDownloading: boolean;
    allMetadataExpanded: boolean;
    infiniteScrollEnabled: boolean;
}

export interface SearchControlsProps {
    placeholder: string;
    showFilterNote: boolean;
    canCopyLink: boolean;
    generatePermalinkUrl: () => string;
}

export interface ResultsSummaryProps {
    displayRange: DisplayRange;
    pageSize: number;
    infiniteScrollEnabled: boolean;
    currentPage: number;
    totalDatasets: number;
}

export interface DatasetSearchInterfaceProps {
    initialFilters: Record<string, string>;
    routeParams?: string[];
}

// Helper types
export interface SortOption {
    label: string;
    value: string;
}

export interface DisplayRange {
    start: number;
    end: number;
    total: number;
}
