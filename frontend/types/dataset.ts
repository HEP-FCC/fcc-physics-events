/**
 * Shared TypeScript types for dataset management
 * Auto-imported by Nuxt 3
 */

/**
 * Sort order for dataset queries
 */
export type SortOrder = "asc" | "desc";

/**
 * Dataset entity with all properties
 * Some properties are readonly (immutable), others can be modified
 */
export interface Dataset {
    readonly dataset_id: number;
    readonly name: string;
    metadata: Record<string, unknown>; // Mutable - can be edited via API
    readonly created_at: string;
    last_edited_at?: string; // Mutable - updated when metadata changes
    readonly accelerator_id?: number | null;
    readonly stage_id?: number | null;
    readonly campaign_id?: number | null;
    readonly detector_id?: number | null;
    readonly detector_name?: string | null;
    readonly campaign_name?: string | null;
    readonly stage_name?: string | null;
    readonly accelerator_name?: string | null;
}

/**
 * API response structure for paginated dataset queries
 */
export interface PaginatedResponse<T = Dataset> {
    readonly total: number;
    readonly items?: T[];
    readonly data?: T[];
}

/**
 * Navigation dropdown item structure
 */
export interface DropdownItem {
    readonly id: number;
    readonly name: string;
}

/**
 * Dropdown type for navigation
 */
export type DropdownType = "stage" | "accelerator" | "campaign" | "detector";

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
 * Navigation dropdown configuration and state
 */
export interface NavigationDropdown {
    items: DropdownItem[]; // Mutable - updated when data is loaded
    isLoading: boolean;
    isOpen: boolean;
    readonly icon: string;
    readonly label: string;
    readonly clearLabel: string;
    readonly apiCall: (filters?: Record<string, string | undefined>) => Promise<DropdownItem[]>;
}

/**
 * Metadata editing state for a single dataset
 */
export interface MetadataEditState {
    isEditing: boolean;
    json: string;
}
