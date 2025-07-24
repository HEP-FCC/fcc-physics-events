/**
 * Entity types for any data structure
 * These types work with any main entity (books, products, etc.)
 * Updated to work with the new backend architecture
 */

import type { Entity } from "~/types/api";

// Re-export the entity types for backward compatibility
export type { Entity } from "~/types/api";

/**
 * Sort order for entity queries
 */
export type SortOrder = "asc" | "desc";

/**
 * API response structure for paginated entity queries
 */
export interface PaginatedResponse<T = Entity> {
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
    loadedPages: Set<number>;
}

/**
 * Sort state for entity ordering
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
    placeholder: string;
    filters: Record<string, unknown>;
    isLoading: boolean;
    isLoadingMore: boolean;
    error: string | null;
    hasMore: boolean;
    isSearching: boolean;
    searchResults: Record<string, unknown>;
    lastSearchQuery: string;
}

/**
 * Sort state for entity ordering
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
 * Selection state for entity management
 */
export interface SelectionState {
    selectedIds: Set<number>;
    selectedEntities: Set<number>;
    expandedMetadata: Set<number>;
    selectAll: boolean;
    isIndeterminate: boolean;
    isDownloading: boolean;
}

/**
 * Metadata editing state for a single entity
 */
export interface MetadataEditState {
    isEditing: boolean;
    editingEntityId: number | null;
    editingData: Record<string, unknown>;
    hasChanges: boolean;
}
