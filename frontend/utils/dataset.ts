import type { Dataset } from "~/types/dataset";
import { getStatusFields } from "./formatting";

/**
 * Dataset-specific utility functions
 */

/**
 * Generate badge items for dataset display (completely dynamic based on schema)
 * This is a pure function that doesn't depend on Vue reactivity
 */
export function getBadgeItems(dataset: Dataset, getNavigationItem: (navType: string) => any) {
    // Generate badges for any field that ends with '_name' and has a value
    // This works regardless of whether navigation config is loaded
    const navigationBadges = Object.entries(dataset)
        .filter(([key, value]) => {
            // Check if this is a navigation field with a value
            return key.endsWith("_name") && value && typeof value === "string" && value.trim() !== "";
        })
        .map(([key, value]) => {
            // Extract the navigation type (remove '_name' suffix)
            const navType = key.replace("_name", "");

            // Get navigation config - will throw if not loaded yet
            const config = getNavigationItem(navType);

            return {
                key: navType,
                label: config.label,
                value: String(value),
                color: config.badgeColor,
                widthClass: "w-auto",
            };
        });

    // Add status badges from metadata
    const statusBadges = getStatusFields(dataset.metadata || {}).map((statusField) => ({
        key: `status_${statusField.key}`,
        label: statusField.label,
        value: String(statusField.value),
        color: statusField.color,
        widthClass: "w-auto",
    }));

    return [...navigationBadges, ...statusBadges];
}
