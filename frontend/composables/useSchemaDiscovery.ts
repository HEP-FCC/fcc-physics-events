/**
 * Schema Discovery Composable
 *
 * This composable manages the runtime configuration of the application
 * based on database schema discovery. It combines static configuration
 * with dynamic schema information from the backend.
 */

import { ref, readonly } from "vue";
import type { RuntimeSchemaConfig } from "~/types/schema";
import { APP_CONFIG } from "~/config/app.config";
import { useApiClient } from "~/composables/useApiClient";

export const useSchemaDiscovery = () => {
    // Reactive state for the runtime configuration
    const runtimeConfig = ref<RuntimeSchemaConfig | null>(null);
    const isLoading = ref(false);
    const error = ref<string | null>(null);
    const configPromise = ref<Promise<RuntimeSchemaConfig> | null>(null);

    /**
     * Get runtime configuration, fetching it if not already loaded
     */
    const getRuntimeConfig = async (): Promise<RuntimeSchemaConfig> => {
        if (runtimeConfig.value) {
            return runtimeConfig.value;
        }

        // If already loading, wait for the existing promise
        if (configPromise.value) {
            return configPromise.value;
        }

        return await fetchAndSetConfig();
    };

    /**
     * Fetch configuration from backend and merge with static overrides
     */
    const fetchAndSetConfig = async (): Promise<RuntimeSchemaConfig> => {
        if (isLoading.value && configPromise.value) {
            return configPromise.value;
        }

        isLoading.value = true;
        error.value = null;

        const promise = (async () => {
            try {
                const { apiClient } = useApiClient();
                const rawSchemaConfig = await apiClient.getSchemaConfiguration();
                const schemaConfig = rawSchemaConfig as unknown as RuntimeSchemaConfig;

                // Merge with static configuration overrides
                const mergedConfig = mergeWithStaticConfig(schemaConfig);

                runtimeConfig.value = mergedConfig;
                return mergedConfig;
            } catch (err) {
                error.value = err instanceof Error ? err.message : "Failed to load configuration";
                throw err;
            } finally {
                isLoading.value = false;
                configPromise.value = null;
            }
        })();

        configPromise.value = promise;
        return promise;
    };

    /**
     * Merge backend schema with static configuration overrides
     */
    const mergeWithStaticConfig = (schemaConfig: RuntimeSchemaConfig): RuntimeSchemaConfig => {
        const merged = { ...schemaConfig };

        // Apply navigation overrides from static config
        if (APP_CONFIG.navigationOverrides) {
            for (const [key, override] of Object.entries(APP_CONFIG.navigationOverrides)) {
                if (merged.navigation[key] && override) {
                    merged.navigation[key] = {
                        ...merged.navigation[key],
                        ...override,
                    };
                }
            }
        }

        // Apply branding overrides
        if (APP_CONFIG.branding) {
            merged.appTitle = APP_CONFIG.branding.title || merged.appTitle;
            merged.searchPlaceholder = APP_CONFIG.branding.defaultTitle || merged.searchPlaceholder;
        }

        return merged;
    };

    /**
     * Get navigation order (list of navigation entity keys)
     */
    const getNavigationOrder = async (): Promise<string[]> => {
        const config = await getRuntimeConfig();
        return config.navigationOrder;
    };

    /**
     * Get navigation configuration for a specific entity
     */
    const getNavigationConfig = async (entityKey: string) => {
        const config = await getRuntimeConfig();
        return config.navigation[entityKey];
    };

    /**
     * Get all navigation configurations
     */
    const getAllNavigationConfigs = async () => {
        const config = await getRuntimeConfig();
        return config.navigation;
    };

    /**
     * Get main table schema information
     */
    const getMainTableSchema = async () => {
        const config = await getRuntimeConfig();
        return config.mainTableSchema;
    };

    /**
     * Get navigation table information
     */
    const getNavigationTable = async (tableKey: string) => {
        const config = await getRuntimeConfig();
        return config.navigationTables[tableKey];
    };

    /**
     * Check if a navigation entity exists
     */
    const hasNavigationEntity = async (entityKey: string): Promise<boolean> => {
        const config = await getRuntimeConfig();
        return entityKey in config.navigation;
    };

    /**
     * Reset configuration (force reload on next access)
     */
    const resetConfig = () => {
        runtimeConfig.value = null;
        error.value = null;
    };

    /**
     * Initialize configuration (call this in app startup)
     */
    const initializeConfig = async () => {
        try {
            await fetchAndSetConfig();
        } catch (err) {
            console.error("Failed to initialize schema configuration:", err);
            // Don't throw - allow app to start with degraded functionality
        }
    };

    return {
        // State
        runtimeConfig: readonly(runtimeConfig),
        isLoading: readonly(isLoading),
        error: readonly(error),

        // Configuration access
        getRuntimeConfig,
        getNavigationOrder,
        getNavigationConfig,
        getAllNavigationConfigs,
        getMainTableSchema,
        getNavigationTable,
        hasNavigationEntity,

        // Control methods
        resetConfig,
        initializeConfig,
        fetchAndSetConfig,
    };
};
