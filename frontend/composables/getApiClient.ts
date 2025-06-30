/**
 * API Client for interacting with the backend services.
 */
import type { PaginatedResponse } from "~/types/event";

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
}

/**
 * Composable function to get an instance of the ApiClient.
 */
export function getApiClient() {
    return new ApiClient();
}
