import {
    formatFieldLabel,
    createEntityDownloadFilename,
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
    // Re-export utility functions for convenience
    return {
        // Pure utility functions (re-exported from utils)
        formatFieldLabel,
        createEntityDownloadFilename,
        downloadAsJsonFile,
        formatFieldName,
        copyToClipboard,
        formatTimestamp,
        formatSizeInGiB,
        isStatusField,
        getStatusBadgeColor,
        getStatusFields,
    };
}
