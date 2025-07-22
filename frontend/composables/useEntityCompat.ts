/**
 * Dynamic schema utilities for working with any entity type.
 * No hardcoded values - everything is derived from the database schema.
 */

export interface DynamicEntity {
    [key: string]: any;
}

/**
 * Get the primary key field name from entities dynamically
 */
export function getPrimaryKeyField(entities: any[]): string | null {
    if (!Array.isArray(entities) || entities.length === 0) {
        return null;
    }

    const firstEntity = entities[0];
    const primaryKeyField = Object.keys(firstEntity).find((key) => key.endsWith("_id"));

    return primaryKeyField || null;
}

/**
 * Get the primary key value from an entity using dynamic field detection
 */
export function getPrimaryKeyValue(entity: any): any {
    if (!entity || typeof entity !== "object") {
        return null;
    }

    const primaryKeyField = Object.keys(entity).find((key) => key.endsWith("_id"));
    return primaryKeyField ? entity[primaryKeyField] : null;
}

/**
 * Extract entity IDs from a list of entities using dynamic primary key detection
 */
export function extractEntityIds(entities: any[]): any[] {
    if (!Array.isArray(entities)) {
        return [];
    }

    const primaryKeyField = getPrimaryKeyField(entities);
    if (!primaryKeyField) {
        return [];
    }

    return entities.map((entity) => entity[primaryKeyField]).filter((id) => id != null);
}

/**
 * Find an entity by its primary key value
 */
export function findEntityById(entities: any[], id: any): any | null {
    const primaryKeyField = getPrimaryKeyField(entities);
    if (!primaryKeyField) {
        return null;
    }

    return entities.find((entity) => entity[primaryKeyField] === id) || null;
}

/**
 * Get entity type from schema or entities
 */
export function getEntityType(entities: any[]): string {
    const primaryKeyField = getPrimaryKeyField(entities);
    if (!primaryKeyField) {
        return "entity";
    }

    // Extract entity type from primary key field (e.g., 'book_id' -> 'book')
    return primaryKeyField.replace("_id", "");
}
