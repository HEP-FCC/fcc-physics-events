/**
 * Generic entity types for any data structure
 * These types work with any main entity (datasets, books, products, etc.)
 */

import type { DynamicEntity } from "~/composables/useEntityCompat";

/**
 * Sort order for entity queries
 */
export type SortOrder = "asc" | "desc";

/**
 * API response structure for paginated entity queries
 */
export interface PaginatedResponse<T = DynamicEntity> {
    data?: T[];
    items?: T[];
    total: number;
    pagination?: {
        currentPage: number;
        totalPages: number;
        pageSize: number;
        total: number;
        hasNext: boolean;
        hasPrev: boolean;
    };
}

/**
 * Pagination state for entity lists
 */
export interface PaginationState {
    currentPage: number;
    pageSize: number;
    totalPages: number;
    totalEntities: number;
    hasNext: boolean;
    hasPrev: boolean;
    // Additional properties used in useDatasetSearch
    totalDatasets: number;
    loadedPages: Set<number>;
}

/**
 * Sort state for entity ordering
 */
export interface SortState {
    field: string;
    order: SortOrder;
    // Additional properties used in useDatasetSearch
    sortBy: string;
    sortOrder: SortOrder;
    availableFields: string[];
    isLoading: boolean;
}

/**
 * Search state for entity filtering
 */
export interface SearchState {
    query: string;
    filters: Record<string, any>;
    isLoading: boolean;
    // Additional properties used in useDatasetSearch
    isLoadingMore: boolean;
    hasMore: boolean;
    error: string | null;
}

/**
 * Sort state for entity queries
 */
export interface SortState {
    field: string;
    order: SortOrder;
    sortBy: string;
    sortOrder: SortOrder;
    availableFields: string[];
    isLoading: boolean;
}

/**
 * Search state for entity filtering
 */
export interface SearchState {
    query: string;
    filters: Record<string, any>;
    isLoading: boolean;
    isLoadingMore: boolean;
    hasMore: boolean;
    error: string | null;
}

/**
 * Entity selection and UI expansion state
 */
export interface SelectionState {
    selectedEntities: Set<number>;
    expandedMetadata: Set<number>;
    isDownloading: boolean;
}

/**
 * Metadata editing state for a single entity
 */
export interface MetadataEditState {
    isEditing: boolean;
    json: string;
    editedJson: string;
    originalMetadata: Record<string, unknown>;
}
