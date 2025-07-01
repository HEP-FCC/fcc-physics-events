/**
 * API Client for interacting with the backend services.
 */
import type { PaginatedResponse, DropdownItem } from "~/types/event";

// Re-export for convenience
export type { DropdownItem };

export class ApiClient {
    private baseUrl: string;

    constructor(baseUrl?: string) {
        const config = useRuntimeConfig();
        this.baseUrl = baseUrl || config.public.apiBaseUrl;
    }

    /**
     * Searches for samples based on a GCLQL query string with pagination.
     * @param query The GCLQL query string.
     * @param limit The maximum number of results to return.
     * @param offset The number of results to skip.
     * @returns A promise that resolves to a paginated response object.
     */
    async searchSamples(query: string, limit: number, offset: number): Promise<PaginatedResponse> {
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
            console.error("Failed to search samples:", error);
            // Re-throw the error so the component can catch it
            throw error;
        }
    }

    /**
     * Fetches all available frameworks for dropdown menu.
     * @param filters Optional filters to apply when fetching frameworks.
     * @returns A promise that resolves to an array of framework dropdown items.
     */
    async getFrameworks(filters?: {
        accelerator_name?: string;
        campaign_name?: string;
        detector_name?: string;
    }): Promise<DropdownItem[]> {
        try {
            const params = new URLSearchParams();
            if (filters?.accelerator_name) params.append("accelerator_name", filters.accelerator_name);
            if (filters?.campaign_name) params.append("campaign_name", filters.campaign_name);
            if (filters?.detector_name) params.append("detector_name", filters.detector_name);

            const url = `${this.baseUrl}/frameworks/${params.toString() ? `?${params.toString()}` : ""}`;
            const response = await fetch(url);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`API error: ${response.status} - ${errorData.detail || "Unknown error"}`);
            }
            return await response.json();
        } catch (error) {
            console.error("Failed to fetch frameworks:", error);
            throw error;
        }
    }

    /**
     * Fetches all available campaigns for dropdown menu.
     * @param filters Optional filters to apply when fetching campaigns.
     * @returns A promise that resolves to an array of campaign dropdown items.
     */
    async getCampaigns(filters?: {
        accelerator_name?: string;
        framework_name?: string;
        detector_name?: string;
    }): Promise<DropdownItem[]> {
        try {
            const params = new URLSearchParams();
            if (filters?.accelerator_name) params.append("accelerator_name", filters.accelerator_name);
            if (filters?.framework_name) params.append("framework_name", filters.framework_name);
            if (filters?.detector_name) params.append("detector_name", filters.detector_name);

            const url = `${this.baseUrl}/campaigns/${params.toString() ? `?${params.toString()}` : ""}`;
            const response = await fetch(url);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`API error: ${response.status} - ${errorData.detail || "Unknown error"}`);
            }
            return await response.json();
        } catch (error) {
            console.error("Failed to fetch campaigns:", error);
            throw error;
        }
    }

    /**
     * Fetches all available detectors for dropdown menu.
     * @param filters Optional filters to apply when fetching detectors.
     * @returns A promise that resolves to an array of detector dropdown items.
     */
    async getDetectors(filters?: {
        accelerator_name?: string;
        framework_name?: string;
        campaign_name?: string;
    }): Promise<DropdownItem[]> {
        try {
            const params = new URLSearchParams();
            if (filters?.accelerator_name) params.append("accelerator_name", filters.accelerator_name);
            if (filters?.framework_name) params.append("framework_name", filters.framework_name);
            if (filters?.campaign_name) params.append("campaign_name", filters.campaign_name);

            const url = `${this.baseUrl}/detectors/${params.toString() ? `?${params.toString()}` : ""}`;
            const response = await fetch(url);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`API error: ${response.status} - ${errorData.detail || "Unknown error"}`);
            }
            return await response.json();
        } catch (error) {
            console.error("Failed to fetch detectors:", error);
            throw error;
        }
    }

    /**
     * Fetches all available accelerators for dropdown menu.
     * @returns A promise that resolves to an array of accelerator dropdown items.
     */
    async getAccelerators(): Promise<DropdownItem[]> {
        try {
            const response = await fetch(`${this.baseUrl}/accelerators/`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`API error: ${response.status} - ${errorData.detail || "Unknown error"}`);
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
