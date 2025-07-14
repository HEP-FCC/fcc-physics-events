import type { Dataset, PaginatedResponse, DropdownItem } from "~/types/dataset";

/**
 * Composable for dataset API client
 * Provides centralized API communication with error handling
 */

/**
 * Centralized API client for all backend communications
 * Handles error states and request management
 * Marked as non-reactive using markRaw for performance
 */
class ApiClient {
    public baseUrl: string;
    private apiAvailable: Ref<boolean>;

    constructor(apiAvailable: Ref<boolean>) {
        const config = useRuntimeConfig();
        // this.baseUrl = config.public.backendUrl as string;
        this.baseUrl = "http://localhost:8000";
        this.apiAvailable = apiAvailable;
    }

    /**
     * Generic request handler with error management
     */
    private async makeRequest<T>(url: string, options: RequestInit = {}, errorContext: string): Promise<T> {
        const fetchOptions: RequestInit = {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, fetchOptions);

            if (response.ok) {
                this.apiAvailable.value = true;
                const result = await response.json();
                return result;
            }

            const error = new Error(`${errorContext}: Server responded with status ${response.status}`) as Error & {
                status?: number;
            };
            error.status = response.status;
            throw error;
        } catch (error) {
            console.error("API ERROR:", { url, error });
            // Only set API as unavailable on connection errors, not on 4xx/5xx
            if (
                error instanceof Error &&
                (error.message.includes("fetch failed") || error.message.includes("Failed to fetch"))
            ) {
                this.apiAvailable.value = false;
            }
            throw error;
        }
    }

    /**
     * Search datasets with pagination and sorting
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

        if (sortBy) params.append("sort_by", sortBy);
        if (sortOrder) params.append("sort_order", sortOrder);

        return this.makeRequest<PaginatedResponse>(
            `${this.baseUrl}/query/?${params}`,
            {
                headers: {
                    "Cache-Control": "no-cache",
                    Pragma: "no-cache",
                    Expires: "0",
                },
            },
            "Failed to search datasets",
        );
    }

    /**
     * Get navigation dropdown options with optional filtering
     */
    async getNavigationOptions(
        entityType: "stage" | "campaign" | "detector" | "accelerator",
        filters?: Record<string, string | undefined>,
    ): Promise<DropdownItem[]> {
        const endpoint = `${entityType}s`;
        let requestUrl = `${this.baseUrl}/${endpoint}/`;

        if (filters) {
            const params = new URLSearchParams();
            Object.entries(filters).forEach(([key, value]) => {
                if (value?.trim()) {
                    params.append(key, value);
                }
            });
            if (params.toString()) {
                requestUrl += `?${params.toString()}`;
            }
        }

        return this.makeRequest<DropdownItem[]>(requestUrl, {}, `Failed to fetch ${entityType}s`);
    }

    /**
     * Download datasets by their IDs
     */
    async downloadDatasetsByIds(datasetIds: number[]): Promise<Dataset[]> {
        return this.makeRequest<Dataset[]>(
            `${this.baseUrl}/authorized/datasets/`,
            {
                method: "POST",
                body: JSON.stringify({
                    dataset_ids: datasetIds,
                }),
            },
            "Failed to download datasets",
        );
    }

    /**
     * Get available fields for sorting
     */
    async getSortingFields(): Promise<{ fields: string[]; count: number; info: string }> {
        return this.makeRequest<{ fields: string[]; count: number; info: string }>(
            `${this.baseUrl}/sorting-fields/`,
            {},
            "Failed to fetch sorting fields",
        );
    }

    /**
     * Update dataset metadata
     */
    async updateDataset(datasetId: number, metadata: Record<string, unknown>): Promise<Dataset> {
        const requestUrl = `${this.baseUrl}/datasets/${datasetId}`;
        return this.makeRequest<Dataset>(
            requestUrl,
            {
                method: "PUT",
                body: JSON.stringify({ metadata }),
            },
            "Failed to update dataset",
        );
    }
}

/**
 * Composable to provide the API client instance
 * Returns a markRaw API client for performance optimization
 */
export function useApiClient() {
    const apiAvailable = useState("api-available", () => true);
    const apiClient = markRaw(new ApiClient(apiAvailable));

    return {
        apiClient,
        apiAvailable: readonly(apiAvailable),
    };
}
