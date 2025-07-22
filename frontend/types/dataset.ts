/**
 * Re-export generic types for dataset context
 * This maintains the interface while using the generic entity system
 */

export type { Dataset } from "~/types/schema";
export type {
    PaginatedResponse,
    PaginationState,
    SortState,
    SearchState,
    SelectionState,
    MetadataEditState,
    SortOrder,
} from "~/types/entity";
