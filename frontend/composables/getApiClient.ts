/**
 * API Client for interacting with the backend services.
 */
import type { Dataset, PaginatedResponse, DropdownItem } from "~/types/dataset";

export class ApiClient {
    private baseUrl: string;

    constructor(baseUrl?: string) {
        const config = useRuntimeConfig();
        this.baseUrl = baseUrl || config.public.apiBaseUrl;
    }

    /**
     * Searches for datasets based on a GCLQL query string with pagination and sorting.
     * @param query The GCLQL query string.
     * @param limit The maximum number of results to return.
     * @param offset The number of results to skip.
     * @param sortBy The field to sort by (optional).
     * @param sortOrder The sort order: 'asc' or 'desc' (optional).
     * @returns A promise that resolves to a paginated response object.
     */
    async searchDatasets(
        query: string,
        limit: number,
        offset: number,
        sortBy?: string,
        sortOrder?: "asc" | "desc",
    ): Promise<PaginatedResponse> {
        try {
            // Use URLSearchParams to properly encode the query string
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

            const response = await fetch(`${this.baseUrl}/query/?${params}`);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`API error: ${response.status} - ${errorData.detail || "Unknown error"}`);
            }

            return await response.json();
        } catch (error) {
            console.error("Failed to search datasets:", error);
            // Re-throw the error so the component can catch it
            throw error;
        }
    }

    /**
     * Generic function to fetch navigation options (stages, campaigns, detectors, accelerators)
     * @param endpoint The API endpoint (stages, campaigns, detectors, accelerators)
     * @param filters Optional filters to apply
     * @returns A promise that resolves to an array of option objects
     */
    private async fetchNavigationOptions(
        endpoint: string,
        filters?: Record<string, string | undefined>,
    ): Promise<DropdownItem[]> {
        try {
            const params = new URLSearchParams();

            // Add all provided filters to the request
            if (filters) {
                Object.entries(filters).forEach(([key, value]) => {
                    if (value) {
                        params.append(key, value);
                    }
                });
            }

            const url = params.toString() ? `${this.baseUrl}/${endpoint}/?${params}` : `${this.baseUrl}/${endpoint}/`;
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`Failed to fetch ${endpoint}:`, error);
            throw error;
        }
    }

    /**
     * Fetches available stages from the API with optional filters.
     */
    async getStages(filters?: {
        accelerator_name?: string;
        campaign_name?: string;
        detector_name?: string;
    }): Promise<DropdownItem[]> {
        return this.fetchNavigationOptions("stages", filters);
    }

    /**
     * Fetches available campaigns from the API with optional filters.
     */
    async getCampaigns(filters?: {
        accelerator_name?: string;
        stage_name?: string;
        detector_name?: string;
    }): Promise<DropdownItem[]> {
        return this.fetchNavigationOptions("campaigns", filters);
    }

    /**
     * Fetches available detectors from the API with optional filters.
     */
    async getDetectors(filters?: {
        accelerator_name?: string;
        stage_name?: string;
        campaign_name?: string;
    }): Promise<DropdownItem[]> {
        return this.fetchNavigationOptions("detectors", filters);
    }

    /**
     * Fetches available accelerators from the API with optional filters.
     */
    async getAccelerators(filters?: {
        stage_name?: string;
        campaign_name?: string;
        detector_name?: string;
    }): Promise<DropdownItem[]> {
        return this.fetchNavigationOptions("accelerators", filters);
    }

    /**
     * Downloads datasets by their IDs as JSON files.
     * @param datasetIds Array of dataset IDs to download
     * @returns A promise that resolves to an array of dataset objects with full details
     */
    async downloadDatasetsByIds(datasetIds: number[]): Promise<Dataset[]> {
        try {
            const response = await fetch(`${this.baseUrl}/datasets/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    dataset_ids: datasetIds,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`API error: ${response.status} - ${errorData.detail || "Unknown error"}`);
            }

            return await response.json();
        } catch (error) {
            console.error("Failed to download datasets:", error);
            throw error;
        }
    }

    /**
     * Fetches available sorting fields from the API.
     * @returns A promise that resolves to the sorting fields response.
     */
    async getSortingFields(): Promise<{ fields: string[]; count: number; info: string }> {
        try {
            const response = await fetch(`${this.baseUrl}/sorting-fields/`);

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error("Failed to fetch sorting fields:", error);
            throw error;
        }
    }
}

/**
 * Composable function to get an instance of the ApiClient.
 */
export function getApiClient() {
    return new ApiClient();
}
