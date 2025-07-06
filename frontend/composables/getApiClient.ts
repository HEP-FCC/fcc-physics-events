/**
 * API Client for interacting with the FCC Physics backend services.
 */
import type { Dataset, PaginatedResponse } from "~/types/dataset";
import type { DropdownItem } from "~/types/navigation";

export class ApiClient {
    private baseUrl: string;

    constructor(baseUrl?: string) {
        const config = useRuntimeConfig();
        this.baseUrl = baseUrl || config.public.apiBaseUrl;
    }

    /**
     * Generic method to handle API requests with consistent error handling
     */
    private async makeRequest<T>(url: string, options: RequestInit = {}, errorContext: string): Promise<T> {
        try {
            const response = await fetch(url, options);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(`${errorContext}: ${response.status} - ${errorData.detail || "Unknown error"}`);
            }

            return await response.json();
        } catch (error) {
            console.error(errorContext, error);
            throw error;
        }
    }

    /**
     * Searches for datasets using GCLQL query with pagination and sorting.
     */
    async searchDatasets(
        query: string,
        limit: number,
        offset: number,
        sortBy?: string,
        sortOrder?: "asc" | "desc",
    ): Promise<PaginatedResponse> {
        const params = new URLSearchParams({
            q: query,
            limit: String(limit),
            offset: String(offset),
        });

        if (sortBy) {
            params.append("sort_by", sortBy);
        }

        if (sortOrder) {
            params.append("sort_order", sortOrder);
        }

        return this.makeRequest<PaginatedResponse>(`${this.baseUrl}/query/?${params}`, {}, "Failed to search datasets");
    }

    /**
     * Fetches navigation options for any entity type with optional filters.
     */
    async getNavigationOptions(
        entityType: "stage" | "campaign" | "detector" | "accelerator",
        filters?: Record<string, string | undefined>,
    ): Promise<DropdownItem[]> {
        const endpoint = `${entityType}s`;
        const url = new URL(`${this.baseUrl}/${endpoint}/`);

        // Add non-empty filter parameters
        if (filters) {
            Object.entries(filters).forEach(([key, value]) => {
                if (value?.trim()) {
                    url.searchParams.append(key, value);
                }
            });
        }

        return this.makeRequest<DropdownItem[]>(url.toString(), {}, `Failed to fetch ${entityType}s`);
    }

    /**
     * Downloads datasets by their IDs.
     */
    async downloadDatasetsByIds(datasetIds: number[]): Promise<Dataset[]> {
        return this.makeRequest<Dataset[]>(
            `${this.baseUrl}/datasets/`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    dataset_ids: datasetIds,
                }),
            },
            "Failed to download datasets",
        );
    }

    /**
     * Fetches available sorting fields from the API.
     */
    async getSortingFields(): Promise<{ fields: string[]; count: number; info: string }> {
        return this.makeRequest<{ fields: string[]; count: number; info: string }>(
            `${this.baseUrl}/sorting-fields/`,
            {},
            "Failed to fetch sorting fields",
        );
    }
}

/**
 * Composable function to get an instance of the ApiClient.
 */
export function getApiClient() {
    return new ApiClient();
}
