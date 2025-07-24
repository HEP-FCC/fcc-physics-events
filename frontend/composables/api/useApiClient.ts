/**
 * Typed API client using Nuxt 3's useFetch
 * Provides type-safe API calls with proper error handling
 */

import type {
    Entity,
    SearchApiResponse,
    ApiError,
    TypedFetchOptions,
    CreateEntityPayload,
    UpdateEntityPayload,
} from "~/types/api";
import type { SearchOptions } from "~/types/composables";

/**
 * Composable for typed API client with Nuxt 3's useFetch
 */
export function useApiClient() {
    const config = useRuntimeConfig();
    const baseUrl = config.public.apiBaseUrl || "http://localhost:8000";

    console.log("DEBUG: baseUrl configured as:", baseUrl);

    /**
     * Generic typed fetch wrapper - handles direct backend responses
     */
    const typedFetch = async <T>(endpoint: string, options: TypedFetchOptions = {}): Promise<T> => {
        try {
            let fullUrl = `${baseUrl}${endpoint}`;

            // Manually construct query string to avoid any $fetch issues
            if (options.query && Object.keys(options.query).length > 0) {
                const queryParams = new URLSearchParams();
                for (const [key, value] of Object.entries(options.query)) {
                    if (value !== undefined && value !== null) {
                        queryParams.append(key, String(value));
                    }
                }
                fullUrl += `?${queryParams.toString()}`;
            }

            console.log("DEBUG: Making request to:", fullUrl);

            const response = await $fetch<T>(fullUrl, {
                method: (options.method || "GET") as "GET" | "POST" | "PUT" | "DELETE",
                body: options.body as Record<string, unknown> | undefined,
                headers: {
                    "Content-Type": "application/json",
                    ...options.headers,
                },
                credentials: "include",
            });

            return response;
        } catch (error: unknown) {
            console.error(`API Error for ${endpoint}:`, error);
            const errorObj = error as Record<string, unknown>;
            const apiError: ApiError = {
                message: (errorObj.message as string) || "API request failed",
                status: (errorObj.statusCode as number) || (errorObj.status as number) || 500,
                details: (errorObj.data as Record<string, unknown>) || undefined,
            };
            throw apiError;
        }
    };

    /**
     * Search entities with typed response - uses /query/ endpoint
     */
    const searchEntities = async (options: SearchOptions = {}): Promise<SearchApiResponse<Entity>> => {
        const queryParams: Record<string, string | number | boolean> = {};

        if (options.query) queryParams.q = options.query;
        if (options.pageSize) queryParams.limit = options.pageSize;
        if (options.page && options.pageSize) {
            queryParams.offset = (options.page - 1) * options.pageSize;
        }
        if (options.sortBy) queryParams.sort_by = options.sortBy;
        if (options.sortOrder) queryParams.sort_order = options.sortOrder;

        const backendResponse = await typedFetch<{ total: number; items: Entity[] }>("/query/", {
            method: "GET",
            query: queryParams,
        });

        console.info("DEBUG:", backendResponse);

        // Transform backend response to match frontend interface
        const result: SearchApiResponse<Entity> = {
            data: backendResponse.items,
            total: backendResponse.total,
            success: true,
            query: options.query,
            filters: options.filters,
            sortBy: options.sortBy,
            sortOrder: options.sortOrder,
        };

        return result;
    };
    /**
     * Get entity by ID
     */
    const getEntityById = async (id: number): Promise<Entity> => {
        return typedFetch<Entity>(`/entities/${id}`);
    };

    /**
     * Get multiple entities by IDs
     */
    const getEntitiesByIds = async (ids: number[]): Promise<Entity[]> => {
        return typedFetch<Entity[]>("/entities/", {
            method: "POST",
            body: { entity_ids: ids },
        });
    };

    /**
     * Create new entity
     */
    const createEntity = async (payload: CreateEntityPayload): Promise<Entity> => {
        return typedFetch<Entity>("/api/entities", {
            method: "POST",
            body: payload,
        });
    };

    /**
     * Update entity
     */
    const updateEntity = async (id: number, payload: UpdateEntityPayload): Promise<Entity> => {
        return typedFetch<Entity>(`/entities/${id}`, {
            method: "PUT",
            body: payload,
        });
    };

    /**
     * Delete entity
     */
    const deleteEntity = async (id: number): Promise<undefined> => {
        return typedFetch<undefined>(`/entities/${id}`, {
            method: "DELETE",
        });
    };

    /**
     * Get sorting fields
     */
    const getSortingFields = async (): Promise<{ fields: string[]; count: number; info: string }> => {
        return typedFetch<{ fields: string[]; count: number; info: string }>("/sorting-fields/");
    };

    /**
     * Get dropdown options for navigation
     */
    const getDropdownOptions = async (type: string): Promise<Array<{ dataset_id: number; name: string }>> => {
        const response = await typedFetch<{ data: Array<{ dataset_id: number; name: string }> }>(
            `/api/dropdown/${type}`,
        );
        return response.data;
    };

    /**
     * Get schema configuration
     */
    const getSchemaConfig = async (): Promise<Record<string, unknown>> => {
        return typedFetch<Record<string, unknown>>("/api/schema");
    };

    /**
     * Download entities as JSON - same as getEntitiesByIds
     */
    const downloadEntitiesByIds = async (ids: number[]): Promise<Entity[]> => {
        return getEntitiesByIds(ids);
    };

    /**
     * Download all filtered entities based on search query
     */
    const downloadFilteredEntities = async (options: SearchOptions = {}): Promise<Entity[]> => {
        const queryParams: Record<string, string | number | boolean> = {};

        if (options.query) queryParams.q = options.query;
        if (options.sortBy) queryParams.sort_by = options.sortBy;
        if (options.sortOrder) queryParams.sort_order = options.sortOrder;

        return typedFetch<Entity[]>("/download-filtered/", {
            method: "GET",
            query: queryParams,
        });
    };

    /**
     * Initiate OAuth login - redirects user to authentication
     */
    const initiateLogin = (): void => {
        window.location.href = `${baseUrl}/login`;
    };

    /**
     * Logout user and get logout URL
     */
    const logoutUser = async (): Promise<{ logout_url: string }> => {
        return typedFetch<{ logout_url: string }>("/logout", {
            method: "GET",
        });
    };

    /**
     * Get session authentication status
     */
    const getSessionStatus = async (): Promise<{ authenticated: boolean; user?: Record<string, unknown> }> => {
        return typedFetch<{ authenticated: boolean; user?: Record<string, unknown> }>("/session-status", {
            method: "GET",
        });
    };

    return {
        // Core methods
        typedFetch,

        // Entity operations
        searchEntities,
        getEntityById,
        getEntitiesByIds,
        createEntity,
        updateEntity,
        deleteEntity,

        // Utility methods
        getSortingFields,
        getDropdownOptions,
        getSchemaConfig,
        downloadEntitiesByIds,
        downloadFilteredEntities,

        // Authentication methods
        initiateLogin,
        logoutUser,
        getSessionStatus,

        // Configuration
        baseUrl,
    };
}
