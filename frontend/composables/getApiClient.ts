/**
 * API Client for interacting with the backend services
 */
export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    // Get from Nuxt config if not provided
    this.baseUrl = baseUrl || useRuntimeConfig().public.apiBaseUrl;
  }

  /**
   * Search for samples based on query
   */
  async searchSamples(query: string): Promise<any> {
    try {
      // Use URLSearchParams to properly encode the query string
      const params = new URLSearchParams({ query });
      const response = await fetch(`${this.baseUrl}/gclql-query/?${params}`);

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      // Get the response data and ensure we return it in the expected format
      const data = await response.json();

      console.log(data);

      // The gclql-query endpoint returns an array directly, so we need to wrap it
      // in an object with a samples property
      return { samples: Array.isArray(data) ? data : [] };
    } catch (error) {
      console.error("Failed to search samples:", error);
      throw error;
    }
  }

  /**
   * Get sample by ID
   */
  async getSampleById(id: number): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/samples/${id}`);

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Failed to get sample ${id}:`, error);
      throw error;
    }
  }
}

// Composable to use the API client
export function getApiClient() {
  const config = useRuntimeConfig();
  return new ApiClient(config.public.apiBaseUrl);
}
