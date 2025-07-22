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
    data: T[];
    pagination: {
        currentPage: number;
        totalPages: number;
        pageSize: number;
        total: number;
        hasNext: boolean;
        hasPrev: boolean;
    };
}

/**
 * Pagination state for entity queries
 */
export interface PaginationState {
    currentPage: number;
    pageSize: number;
    totalPages: number;
    totalEntities: number;
    hasNext: boolean;
    hasPrev: boolean;
}

/**
 * Sort state for entity queries
 */
export interface SortState {
    field: string;
    order: SortOrder;
}

/**
 * Search state for entity filtering
 */
export interface SearchState {
    query: string;
    filters: Record<string, any>;
    isLoading: boolean;
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
    editedJson: string;
    originalMetadata: Record<string, unknown>;
}
