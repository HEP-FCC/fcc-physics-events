/**
 * Utility functions for dynamic schema handling.
 * These functions help the frontend work with any database schema
 * without hardcoded field names.
 */

export interface EntityData {
    [key: string]: any;
}

/**
 * Dynamically detect the primary key field from entity data.
 * Looks for fields ending with '_id' and returns the first one found.
 */
export function getPrimaryKeyField(entityData: EntityData | EntityData[]): string | null {
    const data = Array.isArray(entityData) ? entityData[0] : entityData;

    if (!data || typeof data !== "object") {
        return null;
    }

    // Look for fields ending with '_id' (common convention)
    const idFields = Object.keys(data).filter((key) => key.endsWith("_id"));

    if (idFields.length > 0) {
        return idFields[0]; // Return the first ID field found
    }

    // Fallback: look for 'id' field
    if ("id" in data) {
        return "id";
    }

    return null;
}

/**
 * Get the primary key value from an entity object.
 */
export function getPrimaryKeyValue(entityData: EntityData, primaryKeyField?: string): number | null {
    if (!entityData || typeof entityData !== "object") {
        return null;
    }

    const pkField = primaryKeyField || getPrimaryKeyField(entityData);

    if (!pkField || !(pkField in entityData)) {
        return null;
    }

    const value = entityData[pkField];
    return typeof value === "number" ? value : parseInt(value) || null;
}

/**
 * Determine the entity type from the primary key field name.
 * e.g., 'book_id' -> 'book', 'dataset_id' -> 'dataset'
 */
export function getEntityType(primaryKeyField: string): string {
    if (primaryKeyField.endsWith("_id")) {
        return primaryKeyField.slice(0, -3); // Remove '_id' suffix
    }
    return primaryKeyField;
}

/**
 * Get navigation field names (fields ending with '_name').
 */
export function getNavigationFields(entityData: EntityData): string[] {
    if (!entityData || typeof entityData !== "object") {
        return [];
    }

    return Object.keys(entityData).filter((key) => key.endsWith("_name"));
}

/**
 * Convert entity data to a format expected by components.
 * This ensures backward compatibility while supporting dynamic schemas.
 */
export function normalizeEntityData(entityData: EntityData): EntityData & {
    id: number;
    entityType: string;
    primaryKeyField: string;
} {
    const primaryKeyField = getPrimaryKeyField(entityData);
    const id = primaryKeyField ? getPrimaryKeyValue(entityData, primaryKeyField) : null;
    const entityType = primaryKeyField ? getEntityType(primaryKeyField) : "entity";

    return {
        ...entityData,
        id: id || 0,
        entityType,
        primaryKeyField: primaryKeyField || "id",
    };
}

/**
 * Extract entity IDs from a list of entities dynamically.
 */
export function extractEntityIds(entities: EntityData[]): number[] {
    if (!Array.isArray(entities) || entities.length === 0) {
        return [];
    }

    const primaryKeyField = getPrimaryKeyField(entities);
    if (!primaryKeyField) {
        return [];
    }

    return entities
        .map((entity) => getPrimaryKeyValue(entity, primaryKeyField))
        .filter((id): id is number => id !== null);
}

/**
 * Get the display name for an entity type (plural form).
 * e.g., 'book' -> 'Books', 'dataset' -> 'Datasets'
 */
export function getEntityDisplayName(entityType: string, plural = true): string {
    const singular = entityType.charAt(0).toUpperCase() + entityType.slice(1);

    if (!plural) {
        return singular;
    }

    // Simple pluralization rules
    if (entityType.endsWith("s") || entityType.endsWith("sh") || entityType.endsWith("ch")) {
        return singular + "es";
    } else if (entityType.endsWith("y")) {
        return singular.slice(0, -1) + "ies";
    } else {
        return singular + "s";
    }
}
