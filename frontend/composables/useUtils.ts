import type { Dataset } from "~/types/dataset";
import { APP_CONFIG } from "~/config/app.config";
import { computed, unref, type Ref, type ComputedRef } from "vue";

/**
 * Composable for utility functions
 * Pure utility functions for data formatting and UI helpers
 */

export function useUtils() {
    /**
     * Format field names for display in sorting dropdown
     */
    function formatFieldLabel(field: string): string {
        if (field.startsWith("metadata.")) {
            const metadataKey = field.replace("metadata.", "");
            return `Metadata: ${metadataKey.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}`;
        }
        return field
            .replace(/_/g, " ")
            .replace(/\b\w/g, (l) => l.toUpperCase())
            .replace(" Name", "");
    }

    /**
     * Generate filename for dataset downloads with timestamp
     */
    const createDatasetDownloadFilename = (datasetCount: number): string => {
        const now = new Date();
        const timestamp = now
            .toISOString()
            .slice(0, 19)
            .replace(/[-T:]/g, (match) => (match === "T" ? "_" : "-"));

        const multipleDatasets = datasetCount > 1 ? "datasets" : "dataset";
        return `fcc_physics_datasets-${datasetCount}-${multipleDatasets}-${timestamp}.json`;
    };

    /**
     * Download data as JSON file to user's computer
     */
    const downloadAsJsonFile = (data: unknown, filename: string): void => {
        const jsonContent = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonContent], { type: "application/json" });
        const downloadUrl = URL.createObjectURL(blob);

        const downloadLink = document.createElement("a");
        downloadLink.href = downloadUrl;
        downloadLink.download = filename;
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
        URL.revokeObjectURL(downloadUrl);
    };

    /**
     * Check if a field name represents a status field
     */
    const isStatusField = (key: string): boolean => {
        const normalizedKey = key.toLowerCase();
        return (
            normalizedKey.includes("status") ||
            normalizedKey.includes("state") ||
            normalizedKey.includes("stage") ||
            normalizedKey.includes("phase") ||
            normalizedKey === "health" ||
            normalizedKey === "condition" ||
            normalizedKey === "progress"
        );
    };

    /**
     * Get status badge color based on value
     */
    const getStatusBadgeColor = (
        value: unknown,
    ): "success" | "warning" | "info" | "primary" | "secondary" | "error" | "neutral" => {
        const stringValue = String(value).toLowerCase();

        // Success states
        if (
            stringValue.includes("done") ||
            stringValue.includes("complete") ||
            stringValue.includes("ready") ||
            stringValue.includes("active") ||
            stringValue.includes("running") ||
            stringValue.includes("healthy") ||
            stringValue.includes("ok") ||
            stringValue === "true" ||
            stringValue === "enabled"
        ) {
            return "success";
        }

        // Warning states
        if (
            stringValue.includes("warning") ||
            stringValue.includes("pending") ||
            stringValue.includes("processing") ||
            stringValue.includes("progress") ||
            stringValue.includes("progress") ||
            stringValue.includes("partial")
        ) {
            return "warning";
        }

        // Error states
        if (
            stringValue.includes("error") ||
            stringValue.includes("fail") ||
            stringValue.includes("invalid") ||
            stringValue.includes("stopped") ||
            stringValue.includes("disabled") ||
            stringValue.includes("rejected") ||
            stringValue === "false"
        ) {
            return "error";
        }

        // Info states
        if (
            stringValue.includes("info") ||
            stringValue.includes("draft") ||
            stringValue.includes("scheduled") ||
            stringValue.includes("queued")
        ) {
            return "info";
        }

        // Default neutral
        return "neutral";
    };

    /**
     * Get status fields from metadata
     */
    const getStatusFields = (
        metadata: Record<string, unknown>,
    ): Array<{
        key: string;
        label: string;
        value: unknown;
        color: "success" | "warning" | "info" | "primary" | "secondary" | "error" | "neutral";
    }> => {
        return Object.entries(metadata)
            .filter(([key]) => isStatusField(key))
            .map(([key, value]) => ({
                key,
                label: formatFieldName(key),
                value,
                color: getStatusBadgeColor(value),
            }))
            .sort((a, b) => a.label.localeCompare(b.label));
    };

    /**
     * Generate badge items for dataset display (completely dynamic based on schema)
     */
    function getBadgeItems(dataset: Dataset) {
        /**
         * Generate badge items for dataset display
         */
        function getBadgeItems(dataset: Dataset) {
            const { getNavigationItem } = useNavigationConfig();

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
    }

    /**
     * Create a reactive badge items computed for a dataset
     * This will automatically update when navigation config loads
     */
    function createReactiveBadgeItems(dataset: Ref<Dataset> | ComputedRef<Dataset>) {
        const { navigationConfig } = useNavigationConfig();

        return computed(() => {
            // This will re-run when navigationConfig changes or when dataset changes
            return getBadgeItems(unref(dataset));
        });
    }

    /**
     * Format field names for metadata display
     */
    const formatFieldName = (key: string): string => {
        return key
            .split("_")
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ");
    };

    /**
     * Copy text to clipboard with fallback for older browsers
     */
    async function copyToClipboard(text: string): Promise<void> {
        try {
            await navigator.clipboard.writeText(text);
        } catch {
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";
            textArea.style.opacity = "0";
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand("copy");
            document.body.removeChild(textArea);
        }
    }

    /**
     * Format timestamp for display
     */
    const formatTimestamp = (timestamp: string): string => {
        try {
            const date = new Date(timestamp);
            return date.toLocaleString("en-UK", {
                year: "numeric",
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                hour12: false,
                timeZoneName: "short",
            });
        } catch {
            return timestamp;
        }
    };

    /**
     * Format bytes to GiB for file sizes
     */
    const formatSizeInGiB = (bytes: unknown): string => {
        const bytesNumber = Number(bytes);
        if (isNaN(bytesNumber) || bytesNumber < 0) return "N/A";
        const gigabytes = bytesNumber / (1024 * 1024 * 1024);
        return `${gigabytes.toFixed(2)} GiB`;
    };

    return {
        formatFieldLabel,
        createDatasetDownloadFilename,
        downloadAsJsonFile,
        getBadgeItems,
        formatFieldName,
        copyToClipboard,
        formatTimestamp,
        formatSizeInGiB,
        isStatusField,
        getStatusBadgeColor,
        getStatusFields,
    };
}
