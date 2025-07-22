/**
 * Dynamic schema utilities for working with any entity type.
 * No hardcoded values - everything is derived from the database schema.
 */

import { getPrimaryKeyField } from "./useSchemaUtils";

export interface DynamicEntity {
    [key: string]: any;
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
