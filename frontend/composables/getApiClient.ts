/**
 * API Client for interacting with the backend services.
 */
import type { PaginatedResponse } from "~/types/dataset";

export class ApiClient {
    private baseUrl: string;

    constructor(baseUrl?: string) {
        const config = useRuntimeConfig();
        this.baseUrl = baseUrl || config.public.apiBaseUrl;
    }

    /**
     * Searches for datasets based on a GCLQL query string with pagination.
     * @param query The GCLQL query string.
     * @param limit The maximum number of results to return.
     * @param offset The number of results to skip.
     * @returns A promise that resolves to a paginated response object.
     */
    async searchDatasets(query: string, limit: number, offset: number): Promise<PaginatedResponse> {
        try {
            // Use URLSearchParams to properly encode the query string
            const params = new URLSearchParams({
                q: query,
                limit: String(limit),
                offset: String(offset),
            });
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
     * Fetches available stages from the API with optional filters.
     * @param filters Optional filters to apply
     * @returns A promise that resolves to an array of stage objects.
     */
    async getStages(filters?: {
        accelerator_name?: string;
        campaign_name?: string;
        detector_name?: string;
    }): Promise<Array<{ id: number; name: string }>> {
        try {
            const params = new URLSearchParams();
            if (filters?.accelerator_name) params.append("accelerator_name", filters.accelerator_name);
            if (filters?.campaign_name) params.append("campaign_name", filters.campaign_name);
            if (filters?.detector_name) params.append("detector_name", filters.detector_name);

            const url = params.toString() ? `${this.baseUrl}/stages/?${params}` : `${this.baseUrl}/stages/`;
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error("Failed to fetch stages:", error);
            throw error;
        }
    }

    /**
     * Fetches available campaigns from the API with optional filters.
     * @param filters Optional filters to apply
     * @returns A promise that resolves to an array of campaign objects.
     */
    async getCampaigns(filters?: {
        accelerator_name?: string;
        stage_name?: string;
        detector_name?: string;
    }): Promise<Array<{ id: number; name: string }>> {
        try {
            const params = new URLSearchParams();
            if (filters?.accelerator_name) params.append("accelerator_name", filters.accelerator_name);
            if (filters?.stage_name) params.append("stage_name", filters.stage_name);
            if (filters?.detector_name) params.append("detector_name", filters.detector_name);

            const url = params.toString() ? `${this.baseUrl}/campaigns/?${params}` : `${this.baseUrl}/campaigns/`;
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error("Failed to fetch campaigns:", error);
            throw error;
        }
    }

    /**
     * Fetches available detectors from the API with optional filters.
     * @param filters Optional filters to apply
     * @returns A promise that resolves to an array of detector objects.
     */
    async getDetectors(filters?: {
        accelerator_name?: string;
        stage_name?: string;
        campaign_name?: string;
    }): Promise<Array<{ id: number; name: string }>> {
        try {
            const params = new URLSearchParams();
            if (filters?.accelerator_name) params.append("accelerator_name", filters.accelerator_name);
            if (filters?.stage_name) params.append("stage_name", filters.stage_name);
            if (filters?.campaign_name) params.append("campaign_name", filters.campaign_name);

            const url = params.toString() ? `${this.baseUrl}/detectors/?${params}` : `${this.baseUrl}/detectors/`;
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error("Failed to fetch detectors:", error);
            throw error;
        }
    }

    /**
     * Fetches available accelerators from the API with optional filters.
     * @param filters Optional filters to apply
     * @returns A promise that resolves to an array of accelerator objects.
     */
    async getAccelerators(filters?: {
        stage_name?: string;
        campaign_name?: string;
        detector_name?: string;
    }): Promise<Array<{ id: number; name: string }>> {
        try {
            const params = new URLSearchParams();
            if (filters?.stage_name) params.append("stage_name", filters.stage_name);
            if (filters?.campaign_name) params.append("campaign_name", filters.campaign_name);
            if (filters?.detector_name) params.append("detector_name", filters.detector_name);

            const url = params.toString() ? `${this.baseUrl}/accelerators/?${params}` : `${this.baseUrl}/accelerators/`;
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error("Failed to fetch accelerators:", error);
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
