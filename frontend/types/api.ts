/**
 * Modern API types for entity system
 * Compatible with the dynamic backend architecture
 */

/**
 * Entity from the backend (replaces hardcoded models)
 */
export interface Entity {
    id: number;
    name: string;
    created_at?: string;
    last_edited_at?: string;
    metadata?: Record<string, unknown>;
    [key: string]: unknown; // Allow any additional fields from dynamic schema
}

/**
 * Entity with populated relationship details
 */
export interface EntityWithDetails extends Entity {
    // Relationship fields will be dynamically populated based on schema
    [relationshipField: string]: unknown;
}

/**
 * Generic API response wrapper
 */
export interface ApiResponse<T = unknown> {
    data?: T;
    message?: string;
    error?: string;
}

/**
 * Enhanced paginated response with better typing
 */
export interface PaginatedApiResponse<T = Entity> {
    data: T[];
    total: number;
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
 * Entity creation/update payload
 */
export interface EntityPayload {
    name: string;
    metadata?: Record<string, unknown>;
    [key: string]: unknown; // Dynamic fields based on schema
}

/**
 * Search and filter types
 */
export interface SearchParams {
    q?: string; // Search query
    page?: number;
    pageSize?: number;
    sortBy?: string;
    sortOrder?: "asc" | "desc";
    [filterKey: string]: unknown; // Dynamic filters
}

/**
 * Sort configuration
 */
export interface SortConfig {
    field: string;
    order: "asc" | "desc";
    label?: string;
}

/**
 * Filter configuration for dynamic entity types
 */
export interface FilterConfig {
    key: string;
    label: string;
    type: "select" | "text" | "date" | "number";
    options?: Array<{ id: number | string; name: string }>;
    placeholder?: string;
}

/**
 * Entity selection state
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
 * Entity metadata editing state
 */
export interface MetadataEditState {
    isEditing: boolean;
    editingEntityId: number | null;
    editingData: Record<string, unknown>;
    hasChanges: boolean;
    json: string;
    editedJson: string;
    originalMetadata?: Record<string, unknown>;
}

/**
 * Application state for entity management
 */
export interface EntityManagementState {
    entities: Entity[];
    loading: boolean;
    error: string | null;
    selection: SelectionState;
    metadata: MetadataEditState;
    totalCount: number;
    currentPage: number;
    pageSize: number;
}

/**
 * Bulk operation result
 */
export interface BulkOperationResult {
    success: boolean;
    successCount: number;
    failureCount: number;
    errors?: string[];
    message: string;
    data?: unknown;
    error?: string;
}

// Export Entity as primary interface
