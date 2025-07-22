import type { Dataset } from "~/types/dataset";
import { computed, unref, type Ref, type ComputedRef } from "vue";
import { getBadgeItems } from "~/utils/dataset";
import {
    formatFieldLabel,
    createDatasetDownloadFilename,
    downloadAsJsonFile,
    formatFieldName,
    copyToClipboard,
    formatTimestamp,
    formatSizeInGiB,
    isStatusField,
    getStatusBadgeColor,
    getStatusFields,
} from "~/utils/formatting";

/**
 * Composable for utility functions
 * Provides reactive versions of utility functions and manages state
 */
export function useUtils() {
    /**
     * Generate badge items for dataset display (reactive version)
     */
    function getDatasetBadgeItems(dataset: Dataset) {
        const { getNavigationItem } = useNavigationConfig();
        return getBadgeItems(dataset, getNavigationItem);
    }

    /**
     * Create a reactive badge items computed for a dataset
     * This will automatically update when navigation config loads
     */
    function createReactiveBadgeItems(dataset: Ref<Dataset> | ComputedRef<Dataset>) {
        const { navigationConfig } = useNavigationConfig();

        return computed(() => {
            // This will re-run when navigationConfig changes or when dataset changes
            return getDatasetBadgeItems(unref(dataset));
        });
    }

    // Re-export utility functions for convenience
    return {
        // Pure utility functions (re-exported from utils)
        formatFieldLabel,
        createDatasetDownloadFilename,
        downloadAsJsonFile,
        formatFieldName,
        copyToClipboard,
        formatTimestamp,
        formatSizeInGiB,
        isStatusField,
        getStatusBadgeColor,
        getStatusFields,

        // Composable-specific functions
        getBadgeItems: getDatasetBadgeItems,
        createReactiveBadgeItems,
    };
}
