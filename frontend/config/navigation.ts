/**
 * Centralized navigation configuration
 * This file defines the dropdown order and configuration for the entire application
 * When adding a new dropdown, only this file needs to be updated
 */

import type { DropdownType } from "~/types/dataset";

/**
 * The order of dropdowns in the navigation hierarchy
 * This order is used throughout the application for:
 * - URL path parsing (/stage/accelerator/campaign/detector)
 * - Navigation menu rendering
 * - Filter dependencies
 */
export const DROPDOWN_ORDER: readonly DropdownType[] = ["stage", "accelerator", "campaign", "detector"] as const;

/**
 * Navigation dropdown configuration including icons, labels, and colors
 */
export const NAVIGATION_CONFIG = {
    stage: {
        icon: "i-heroicons-cpu-chip",
        label: "Stage",
        clearLabel: "Clear Stage",
        badgeColor: "success" as const,
    },
    accelerator: {
        icon: "i-heroicons-bolt",
        label: "Accelerator",
        clearLabel: "Clear Accelerator",
        badgeColor: "neutral" as const,
    },
    campaign: {
        icon: "i-heroicons-calendar-days",
        label: "Campaign",
        clearLabel: "Clear Campaign",
        badgeColor: "warning" as const,
    },
    detector: {
        icon: "i-heroicons-beaker",
        label: "Detector",
        clearLabel: "Clear Detector",
        badgeColor: "info" as const,
    },
} as const;

/**
 * Helper function to parse route parameters into path object
 * Uses the centralized dropdown order
 */
export function parseRouteToPath(routeParams: string[]): Record<string, string | null> {
    const pathObj: Record<string, string | null> = {};
    DROPDOWN_ORDER.forEach((type, index) => {
        pathObj[type] = routeParams[index] || null;
    });
    return pathObj;
}

/**
 * Helper function to parse route parameters into API filters
 * Uses the centralized dropdown order
 */
export function parseRouteToFilters(routeParams: string[]): Record<string, string> {
    const filters: Record<string, string> = {};
    DROPDOWN_ORDER.forEach((type, index) => {
        if (routeParams.length > index && routeParams[index]) {
            filters[`${type}_name`] = routeParams[index];
        }
    });
    return filters;
}

/**
 * Helper function to build a navigation path from selections
 * Uses the centralized dropdown order
 */
export function buildNavigationPath(
    currentPath: Record<string, string | null>,
    type: DropdownType,
    value: string,
): string {
    const typeIndex = DROPDOWN_ORDER.indexOf(type);
    const pathParts = DROPDOWN_ORDER.map((t) => currentPath[t]);

    const newPathParts = pathParts.slice(0, typeIndex);
    newPathParts.push(value);

    const filteredParts = newPathParts.filter((p) => p);
    return filteredParts.length === 0 ? "/" : `/${filteredParts.join("/")}`;
}

/**
 * Helper function to clear a selection and build the resulting path
 * Uses the centralized dropdown order
 */
export function buildClearPath(currentPath: Record<string, string | null>, type: DropdownType): string {
    const typeIndex = DROPDOWN_ORDER.indexOf(type);
    const pathParts = DROPDOWN_ORDER.map((t) => currentPath[t]);

    const newPathParts = pathParts.slice(0, typeIndex).filter((p) => p);
    return newPathParts.length === 0 ? "/" : `/${newPathParts.join("/")}`;
}

/**
 * Generate page title from active filters
 * Uses the centralized dropdown order
 */
export function generatePageTitle(filters: Record<string, string>): string {
    const filterNames = DROPDOWN_ORDER.map((type) => filters[`${type}_name`]).filter(Boolean);

    if (filterNames.length > 0) {
        return `FCC Physics Datasets - ${filterNames.join(" / ")}`;
    }
    return "FCC Physics Datasets Search";
}

/**
 * Generate page description from active filters
 */
export function generatePageDescription(filters: Record<string, string>): string {
    if (Object.keys(filters).length > 0) {
        const filterDesc = Object.entries(filters)
            .map(([key, value]) => `${key.replace("_", " ")}: ${value}`)
            .join(", ");
        return `Search FCC physics datasets filtered by ${filterDesc}`;
    }
    return "Search and explore FCC physics simulation datasets and data";
}
