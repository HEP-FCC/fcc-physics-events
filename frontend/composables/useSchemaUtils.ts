/**
 * Utility functions for dynamic schema handling.
 * These functions help the frontend work with any database schema
 * without hardcoded field names.
 */

export interface EntityData {
    [key: string]: unknown;
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
    return typeof value === "number" ? value : (typeof value === "string" ? parseInt(value, 10) : null) || null;
}

/**
 * Determine the entity type from the primary key field name.
 * e.g., 'book_id' -> 'book', 'product_id' -> 'product'
 */
export function getEntityType(primaryKeyField: string): string {
    if (primaryKeyField.endsWith("_id")) {
        return primaryKeyField.slice(0, -3); // Remove '_id' suffix
    }
    return primaryKeyField;
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
