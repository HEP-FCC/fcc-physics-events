import { computed } from "vue";
import { getApiClient } from "./getApiClient";
import type { DropdownItem } from "~/types/navigation";

export interface NavigationDropdownConfig {
    items: DropdownItem[];
    isLoading: boolean;
    isOpen: boolean;
    icon: string;
    label: string;
    clearLabel: string;
    apiCall: (filters?: Record<string, string | undefined>) => Promise<DropdownItem[]>;
}

/**
 * Centralized navigation configuration and utilities.
 * Manages the navigation dropdown structure and URL parsing logic.
 */
export function useNavigationConfig() {
    const apiClient = getApiClient();

    // Navigation dropdown configuration - order determines URL structure
    const navigationConfig = {
        stage: {
            icon: "i-heroicons-cpu-chip",
            label: "Stage",
            clearLabel: "Clear Stage",
            apiCall: (filters?: Record<string, string | undefined>) => apiClient.getNavigationOptions("stage", filters),
        },
        campaign: {
            icon: "i-heroicons-calendar-days",
            label: "Campaign",
            clearLabel: "Clear Campaign",
            apiCall: (filters?: Record<string, string | undefined>) =>
                apiClient.getNavigationOptions("campaign", filters),
        },
        detector: {
            icon: "i-heroicons-beaker",
            label: "Detector",
            clearLabel: "Clear Detector",
            apiCall: (filters?: Record<string, string | undefined>) =>
                apiClient.getNavigationOptions("detector", filters),
        },
    } as const;

    // Derive the DropdownType from the navigationConfig keys
    type DropdownType = keyof typeof navigationConfig;

    const dropdownKeys = computed(() => Object.keys(navigationConfig) as DropdownType[]);

    /**
     * Parse route parameters into filters object for API queries.
     * Converts URL segments like ['IDEA', 'spring2024'] into { detector_name: 'IDEA', campaign_name: 'spring2024' }
     */
    function parseRouteParams(params: string[]): Record<string, string> {
        const filters: Record<string, string> = {};

        dropdownKeys.value.forEach((type, index) => {
            if (params.length > index && params[index]) {
                filters[`${type}_name`] = params[index];
            }
        });

        return filters;
    }

    /**
     * Parse route parameters for navigation menu display.
     * Returns which value is selected for each dropdown type.
     */
    function parseCurrentPath(params: string[]): Record<DropdownType, string | null> {
        const pathObj: Record<DropdownType, string | null> = {} as Record<DropdownType, string | null>;

        dropdownKeys.value.forEach((type, index) => {
            pathObj[type] = params[index] || null;
        });

        return pathObj;
    }

    /**
     * Generate page title from active filters.
     */
    function generatePageTitle(filters: Record<string, string>): string {
        const filterNames = dropdownKeys.value.map((type) => filters[`${type}_name`]).filter(Boolean);

        if (filterNames.length > 0) {
            return `FCC Physics Datasets - ${filterNames.join(" / ")}`;
        }
        return "FCC Physics Datasets Search";
    }

    /**
     * Generate page description from active filters.
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
