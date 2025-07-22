/**
 * Dropdown Preloader
 *
 * Handles concurrent preloading of dropdown data for all navigation types
 * to improve user experience by eliminating loading delays when clicking dropdowns.
 */

import { ref, readonly } from "vue";

const isPreloading = ref(false);
const preloadedTypes = ref<Set<string>>(new Set());

export function useDropdownPreloader() {
    const { apiClient } = useApiClient();

    /**
     * Preload dropdown data for all specified navigation types concurrently
     */
    const preloadDropdownData = async (navigationOrder: string[]): Promise<void> => {
        if (isPreloading.value || navigationOrder.length === 0) {
            return;
        }

        isPreloading.value = true;

        try {
            console.debug(`Starting dropdown preloading for ${navigationOrder.length} types:`, navigationOrder);

            // Create concurrent API calls for all navigation types
            const preloadPromises = navigationOrder.map(async (type: string) => {
                try {
                    const response = await fetch(`${apiClient.baseUrl}/api/dropdown/${type}`);
                    if (response.ok) {
                        const data = await response.json();
                        preloadedTypes.value.add(type);
                        console.debug(`Preloaded ${type}: ${data.data?.length || 0} items`);
                        return { type, success: true, count: data.data?.length || 0 };
                    } else {
                        console.warn(`Failed to preload ${type}: ${response.status}`);
                        return { type, success: false, error: response.status };
                    }
                } catch (error) {
                    console.warn(`Error preloading ${type}:`, error);
                    return { type, success: false, error };
                }
            });

            // Wait for all preload operations to complete
            const results = await Promise.allSettled(preloadPromises);

            // Log summary
            const successful = results.filter((r) => r.status === "fulfilled" && r.value.success).length;
            console.debug(`Dropdown preloading completed: ${successful}/${navigationOrder.length} successful`);
        } catch (error) {
            console.warn("Error during dropdown preloading:", error);
        } finally {
            isPreloading.value = false;
        }
    };

    /**
     * Check if a specific type has been preloaded
     */
    const isTypePreloaded = (type: string): boolean => {
        return preloadedTypes.value.has(type);
    };

    /**
     * Clear preload cache
     */
    const clearPreloadCache = (): void => {
        preloadedTypes.value.clear();
    };

    return {
        preloadDropdownData,
        isPreloading: readonly(isPreloading),
        preloadedTypes: readonly(preloadedTypes),
        isTypePreloaded,
        clearPreloadCache,
    };
}
