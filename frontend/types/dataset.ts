/**
 * Shared TypeScript types for dataset management
 * Auto-imported by Nuxt 3
 */

import type { Dataset as SchemaDataset } from "~/types/schema";

/**
 * Re-export Dataset for convenience
 */
export type Dataset = SchemaDataset;

/**
 * Sort order for dataset queries
 */
export type SortOrder = "asc" | "desc";

/**
 * API response structure for paginated dataset queries
 */
export interface PaginatedResponse<T = Dataset> {
    readonly total: number;
    readonly items?: T[];
    readonly data?: T[];
}

/**
 * Search operation state management
 */
export interface SearchState {
    isLoading: boolean;
    isLoadingMore: boolean;
    error: string | null;
    hasMore: boolean;
}

/**
 * Pagination state for both infinite scroll and traditional pagination
 */
export interface PaginationState {
    currentPage: number;
    pageSize: number;
    totalDatasets: number;
    totalPages: number;
    loadedPages: Set<number>;
}

/**
 * Sorting configuration and available fields
 */
export interface SortState {
    sortBy: string;
    sortOrder: SortOrder;
    availableFields: string[]; // Mutable - updated when fields are fetched
    isLoading: boolean;
}

/**
 * Dataset selection and UI expansion state
 */
export interface SelectionState {
    selectedDatasets: Set<number>;
    expandedMetadata: Set<number>;
    isDownloading: boolean;
}

/**
 * Metadata editing state for a single dataset
 */
export interface MetadataEditState {
    isEditing: boolean;
    json: string;
}
