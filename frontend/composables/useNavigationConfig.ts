/**
 * Navigation Configuration Management
 *
 * This composable manages the dynamic fetching of navigation configuration
 * from the backend schema endpoint. All UI elements (colors, icons, labels)
 * are derived from app config, not from backend.
 */

import type { SchemaInfo } from "~/types/schema";
import { APP_CONFIG } from "~/config/app.config";

interface NavigationConfig {
    order: string[];
    menu: Record<
        string,
        {
            columnName: string;
            orderIndex: number;
        }
    >;
}

export const useNavigationConfig = () => {
    const { apiClient } = useApiClient();

    // Reactive state for navigation configuration
    const navigationConfig = ref<NavigationConfig>({
        order: [],
        menu: {},
    });

    const isLoading = ref(false);
    const error = ref<string | null>(null);

    /**
     * Fetch navigation configuration from backend schema endpoint
     */
    const fetchNavigationConfig = async (): Promise<void> => {
        if (isLoading.value) return;

        try {
            isLoading.value = true;
            error.value = null;

            const response = (await apiClient.getSchemaConfiguration()) as unknown as SchemaInfo;

            if (response.navigation_config) {
                navigationConfig.value = {
                    order: response.navigation_config.order || [],
                    menu: response.navigation_config.menu || {},
                };
            } else {
                // Fallback: use foreign_keys as navigation order if no config
                const foreignKeys = response.foreign_keys || [];
                const fallbackMenu: Record<string, { columnName: string; orderIndex: number }> = {};

                foreignKeys.forEach((fk: string, index: number) => {
                    const key = fk.replace("_id", "");
                    fallbackMenu[key] = {
                        columnName: fk,
                        orderIndex: index,
                    };
                });

                navigationConfig.value = {
                    order: foreignKeys.map((fk: string) => fk.replace("_id", "")),
                    menu: fallbackMenu,
                };
            }
        } catch (err) {
            error.value = err instanceof Error ? err.message : "Failed to fetch navigation config";
            console.error("Failed to fetch navigation configuration:", err);

            // Fallback to empty configuration
            navigationConfig.value = {
                order: [],
                menu: {},
            };
        } finally {
            isLoading.value = false;
        }
    };

    // Auto-initialize on first use
    if (navigationConfig.value.order.length === 0 && !isLoading.value) {
        fetchNavigationConfig();
    }

    /**
     * Get navigation order
     */
    const getNavigationOrder = (): string[] => {
        return navigationConfig.value.order;
    };

    /**
     * Check if navigation configuration is ready
     */
    const isNavigationReady = (): boolean => {
        return !isLoading.value && navigationConfig.value.order.length > 0;
    };

    /**
     * Get navigation menu configuration
     */
    const getNavigationMenu = () => {
        return navigationConfig.value.menu;
    };

    /**
     * Get configuration for a specific navigation type with derived UI elements
     */
    const getNavigationItem = (type: string) => {
        const menuConfig = navigationConfig.value.menu[type];

        if (!menuConfig) {
            throw new Error(
                `Navigation type '${type}' not found in configuration. Available types: ${Object.keys(
                    navigationConfig.value.menu,
                ).join(", ")}. Is navigation initialized?`,
            );
        }

        const orderIndex = menuConfig.orderIndex;
        const colors = APP_CONFIG.ui.defaultBadgeColors;

        return {
            icon: APP_CONFIG.ui.defaultIcon, // Use hardcoded folder icon for all items
            label: type.charAt(0).toUpperCase() + type.slice(1).replace(/[_-]/g, " "),
            badgeColor: colors[orderIndex % colors.length],
            columnName: menuConfig.columnName,
        };
    };

    /**
     * Initialize navigation configuration if not already loaded
     */
    const initializeNavigation = async (): Promise<void> => {
        if (navigationConfig.value.order.length === 0) {
            await fetchNavigationConfig();
        }
    };

    return {
        navigationConfig: readonly(navigationConfig),
        isLoading: readonly(isLoading),
        error: readonly(error),
        isNavigationReady,
        fetchNavigationConfig,
        getNavigationOrder,
        getNavigationMenu,
        getNavigationItem,
        initializeNavigation,
    };
};
