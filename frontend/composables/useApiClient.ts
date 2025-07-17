import type { Dataset, PaginatedResponse, DropdownItem } from "~/types/dataset";
import { retryWithBackoff, type RetryOptions } from "~/composables/useRetry";

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
        this.baseUrl = config.public.apiBaseUrl as string;
        this.apiAvailable = apiAvailable;
    }

    /**
     * Generic request handler with error management and exponential backoff retries
     */
    private async makeRequest<T>(
        url: string,
        options: RequestInit = {},
        errorContext: string,
        retryOptions?: RetryOptions,
    ): Promise<T> {
        // Get auth token if available
        const token = localStorage.getItem("auth_token");

        const fetchOptions: RequestInit = {
            ...options,
            credentials: "include", // Include cookies for session management
            headers: {
                "Content-Type": "application/json",
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
                ...options.headers,
            },
        };

        // Define the actual fetch operation
        const fetchOperation = async (): Promise<T> => {
            console.log(`🌐 API Request: ${fetchOptions.method || "GET"} ${url}`, {
                options: fetchOptions,
                context: errorContext,
            });
            const response = await fetch(url, fetchOptions);

            if (response.ok) {
                this.apiAvailable.value = true;
                const result = await response.json();
                console.log(`✅ API Response: ${fetchOptions.method || "GET"} ${url}`, {
                    status: response.status,
                    result,
                });
                return result;
            }

            // Handle specific error cases
            if (response.status === 401) {
                console.error(`❌ API Error: ${errorContext}`, {
                    status: response.status,
                    url,
                    error: "Authentication failed",
                });
                const error = new Error(`Authentication failed: ${errorContext}`) as Error & {
                    status?: number;
                };
                error.status = response.status;
                throw error;
            }

            if (response.status === 403) {
                console.error(`❌ API Error: ${errorContext}`, {
                    status: response.status,
                    url,
                    error: "Access forbidden",
                });
                const error = new Error(`Access forbidden: ${errorContext}`) as Error & {
                    status?: number;
                };
                error.status = response.status;
                throw error;
            }

            console.error(`❌ API Error: ${errorContext}`, {
                status: response.status,
                url,
                error: `Server responded with status ${response.status}`,
            });
            const error = new Error(`${errorContext}: Server responded with status ${response.status}`) as Error & {
                status?: number;
            };
            error.status = response.status;
            throw error;
        };

        // Default retry options for API calls
        const defaultRetryOptions: RetryOptions = {
            maxAttempts: 5,
            initialDelay: 200,
            maxDelay: 10000,
            backoffMultiplier: 2,
            useJitter: true,
            shouldRetry: (error: Error) => {
                // Retry on network errors and 5xx server errors
                if (
                    error.message.includes("fetch failed") ||
                    error.message.includes("Failed to fetch") ||
                    error.message.includes("Network Error")
                ) {
                    return true;
                }

                // Retry on server errors (5xx) but not on client errors (4xx)
                if ("status" in error && typeof error.status === "number") {
                    return error.status >= 500 && error.status < 600;
                }

                return false;
            },
        };

        const finalRetryOptions = { ...defaultRetryOptions, ...retryOptions };

        try {
            const retryResult = await retryWithBackoff(fetchOperation, finalRetryOptions);
            return retryResult.result;
        } catch (error) {
            // Only set API as unavailable on connection errors, not on 4xx/5xx
            if (
                error instanceof Error &&
                (error.message.includes("fetch failed") ||
                    error.message.includes("Failed to fetch") ||
                    error.message.includes("Network Error"))
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
     * Download datasets by their IDs with aggressive retry policy
     * Downloads are critical operations that may need more retry attempts
     */
    async downloadDatasetsByIds(datasetIds: number[]): Promise<Dataset[]> {
        return this.makeRequest<Dataset[]>(
            `${this.baseUrl}/datasets/`,
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
        // TODO: define the cookie name better
        const cookie = Object(useCookie("fcc-physics-events-web", { secure: true }).value);

        return this.makeRequest<Dataset>(
            requestUrl,
            {
                method: "PUT",
                body: JSON.stringify({ metadata }),
                headers: { Authorization: `Bearer ${cookie.token}` },
            },
            "Failed to update dataset",
        );
    }

    /**
     * Update dataset metadata with authentication
     */
    async updateDatasetWithAuth(
        datasetId: number,
        metadata: Record<string, unknown>,
        accessToken: string,
    ): Promise<Dataset> {
        const requestUrl = `${this.baseUrl}/datasets/${datasetId}`;
        return this.makeRequest<Dataset>(
            requestUrl,
            {
                method: "PUT",
                headers: {
                    Authorization: accessToken,
                },
                body: JSON.stringify({ metadata }),
            },
            "Failed to update dataset",
        );
    }

    /**
     * Initiate OAuth login - redirects user to authentication
     */
    initiateLogin(): void {
        window.location.href = `${this.baseUrl}/login`;
    }

    /**
     * Logout user
     */
    async logout(): Promise<void> {
        try {
            await this.makeRequest(`${this.baseUrl}/logout`, { method: "POST" }, "Failed to logout");
        } catch (error) {
            console.error("Logout error:", error);
            // Don't throw here as we want to clear session even if server call fails
        }
    }

    /**
     * Get current user information
     */
    async getCurrentUser(token?: string): Promise<{ user?: any; authenticated: boolean }> {
        const options: RequestInit = {};
        if (token) {
            options.headers = { Authorization: `Bearer ${token}` };
        }
        return this.makeRequest<{ user?: any; authenticated: boolean }>(
            `${this.baseUrl}/user`,
            options,
            "Failed to get user info",
        );
    }

    /**
     * Get access token validation (for checking if current token is valid)
     */
    async getAccessToken(): Promise<{
        access_token: string;
        token_type: string;
        user: any;
    }> {
        return this.makeRequest<{
            access_token: string;
            token_type: string;
            user: any;
        }>(`${this.baseUrl}/auth/token`, {}, "Failed to validate access token");
    }

    async loginAndGetJwtToken(): Promise<{}> {
        return this.makeRequest<{}>(`${this.baseUrl}/login`, {}, "Failed to login.");
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
