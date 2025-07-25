/**
 * Entity Badge Management Composable
 *
 * Provides optimized badge color assignment and caching to prevent
 * the gray->colored flash when entities load before navigation config.
 */

import type { Entity } from "~/types/entity";
import type { BadgeColor } from "~/config/app.config";
import { getBadgeColorWithFallback, getDeterministicBadgeColor } from "~/utils/badgeColors";
import { APP_CONFIG } from "~/config/app.config";

interface BadgeInfo {
    key: string;
    label: string;
    value: string;
    color: BadgeColor;
    filterKey: string;
}

/**
 * Composable for managing entity badges with optimized color assignment
 */
export const useEntityBadges = () => {
    const { getNavigationItem, isNavigationReady, getNavigationOrder } = useNavigationConfig();
    const { formatFieldName, getStatusFields } = useUtils();

    // Cache for badge colors to avoid recalculation
    const badgeColorCache = new Map<string, BadgeColor>();

    /**
     * Clear the badge color cache (useful when navigation config changes)
     */
    const clearBadgeColorCache = () => {
        badgeColorCache.clear();
    };

    /**
     * Get optimized badge color for a navigation type
     */
    const getBadgeColor = (navType: string): BadgeColor => {
        // Check cache first
        if (badgeColorCache.has(navType)) {
            return badgeColorCache.get(navType)!;
        }

        // Always use deterministic color for consistency
        const color = getDeterministicBadgeColor(navType);

        // Cache the result
        badgeColorCache.set(navType, color);
        return color;
    };

    /**
     * Get all badge information for an entity
     */
    const getEntityBadges = (entity: Entity, activeFilters?: Record<string, string>): BadgeInfo[] => {
        // Generate navigation badges for any field ending with '_name' that has a value
        const navigationBadges = Object.entries(entity)
            .filter(([key, value]) => {
                return key.endsWith("_name") && value && typeof value === "string" && value.trim() !== "";
            })
            .map(([key, value]) => {
                const navType = key.replace("_name", "");
                const color = getBadgeColor(navType);

                // Get label from navigation config or use formatted fallback
                let label: string;
                try {
                    const config = getNavigationItem(navType);
                    label = config.label;
                } catch {
                    label = formatFieldName(navType);
                }

                return {
                    key: navType ? String(navType) : "unknown",
                    label: String(label || formatFieldName(navType || "unknown")),
                    value: String(value || ""),
                    color,
                    filterKey: key,
                };
            })
            .filter((badge) => {
                // Filter out badges that match currently active filters
                const activeFilterValue = activeFilters?.[badge.filterKey];
                return !activeFilterValue || activeFilterValue !== badge.value;
            });

        // Add status badges from metadata (these are always shown as they're not navigation filters)
        const statusBadges = getStatusFields(entity.metadata || {}).map((statusField) => ({
            key: statusField.key ? `status_${String(statusField.key)}` : "status_unknown",
            label: String(statusField.label || "Unknown"),
            value: String(statusField.value || ""),
            color: (statusField.color as BadgeColor) || "neutral",
            filterKey: `status_${statusField.key}`, // Not used for filtering but kept for consistency
        }));

        return [...navigationBadges, ...statusBadges];
    };

    /**
     * Preload badge colors for known navigation types
     * This can be called early to warm up the cache
     */
    const preloadBadgeColors = (navigationTypes: string[]) => {
        navigationTypes.forEach((type) => {
            getBadgeColor(type);
        });
    };

    return {
        getEntityBadges,
        getBadgeColor,
        clearBadgeColorCache,
        preloadBadgeColors,
    };
};
