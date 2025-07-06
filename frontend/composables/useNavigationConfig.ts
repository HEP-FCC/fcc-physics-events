import { computed } from "vue";
import { getApiClient } from "./getApiClient";
import type { DropdownItem } from "~/types/dataset";

export interface NavigationDropdownConfig {
    items: DropdownItem[];
    isLoading: boolean;
    isOpen: boolean;
    icon: string;
    label: string;
    clearLabel: string;
    apiCall: (filters?: Record<string, unknown>) => Promise<DropdownItem[]>;
}

/**
 * Centralized navigation configuration
 * This defines the order and configuration of all navigation dropdowns
 * Adding/removing items here automatically updates the DropdownType
 */
export function useNavigationConfig() {
    const apiClient = getApiClient();

    // Define navigation dropdowns in the desired order
    // This is the SINGLE SOURCE OF TRUTH for navigation types
    const navigationConfig = {
        stage: {
            icon: "i-heroicons-cpu-chip",
            label: "Stage",
            clearLabel: "Clear Stage",
            apiCall: apiClient.getStages.bind(apiClient),
        },
        campaign: {
            icon: "i-heroicons-calendar-days",
            label: "Campaign",
            clearLabel: "Clear Campaign",
            apiCall: apiClient.getCampaigns.bind(apiClient),
        },
        detector: {
            icon: "i-heroicons-beaker",
            label: "Detector",
            clearLabel: "Clear Detector",
            apiCall: apiClient.getDetectors.bind(apiClient),
        },
    } as const; // 'as const' ensures TypeScript treats this as a literal type

    // Derive the DropdownType from the navigationConfig keys
    type DropdownType = keyof typeof navigationConfig;

    // Get ordered dropdown keys for consistent navigation hierarchy
    const dropdownKeys = computed(() => Object.keys(navigationConfig) as DropdownType[]);

    /**
     * Parse route parameters into typed filters object
     */
    function parseRouteParams(params: string[]): Record<string, string> {
        const filters: Record<string, string> = {};

        dropdownKeys.value.forEach((type, index) => {
            if (params.length > index && params[index]) {
                const filterKey = `${type}_name`;
                filters[filterKey] = params[index];
            }
        });

        return filters;
    }

    /**
     * Parse route parameters into currentPath object (for navigation menu)
     */
    function parseCurrentPath(params: string[]): Record<DropdownType, string | null> {
        const pathObj: Record<DropdownType, string | null> = {} as Record<DropdownType, string | null>;

        dropdownKeys.value.forEach((type, index) => {
            pathObj[type] = params[index] || null;
        });

        return pathObj;
    }

    /**
     * Generate readable page title from active filters
     */
    function generatePageTitle(filters: Record<string, string>): string {
        const filterNames = dropdownKeys.value.map((type) => filters[`${type}_name`]).filter(Boolean);

        if (filterNames.length > 0) {
            return `FCC Physics Datasets - ${filterNames.join(" / ")}`;
        }
        return "FCC Physics Datasets Search";
    }

    /**
     * Generate page description from active filters
     */
    function generatePageDescription(filters: Record<string, string>): string {
        if (Object.keys(filters).length > 0) {
            const filterDesc = Object.entries(filters)
                .map(([key, value]) => `${key.replace("_", " ")}: ${value}`)
                .join(", ");
            return `Search FCC physics datasets filtered by ${filterDesc}`;
        }
        return "Search and explore FCC physics simulation datasets and data";
    }

    return {
        navigationConfig,
        dropdownKeys,
        parseRouteParams,
        parseCurrentPath,
        generatePageTitle,
        generatePageDescription,
    };
}

// Export the derived DropdownType for use in other files
export type DropdownType = keyof ReturnType<typeof useNavigationConfig>["navigationConfig"];
