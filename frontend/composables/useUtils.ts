import type { Dataset } from "~/types/dataset";
import { APP_CONFIG } from "~/config/app.config";

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
     * Get badge color for navigation dropdown types
     */
    const getBadgeColor = (type: string): "success" | "warning" | "info" | "primary" => {
        const colorMap: Record<string, "success" | "warning" | "info"> = {
            stage: "success",
            campaign: "warning",
            detector: "info",
        };
        return colorMap[type] || "primary";
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
     * Generate badge items for dataset display
     */
    function getBadgeItems(dataset: Dataset) {
        // Generate standard badges from app config navigation overrides
        const standardBadges = Object.entries(APP_CONFIG.navigationOverrides).map(([dropdownType, config]) => {
            const fieldName = `${dropdownType}_name` as keyof Dataset;

            return {
                key: dropdownType,
                label: config.label,
                value: dataset[fieldName],
                color: config.badgeColor,
                widthClass: getWidthClass(dropdownType),
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

        return [...standardBadges, ...statusBadges];
    }

    /**
     * Get appropriate width class for different dropdown types
     */
    function getWidthClass(dropdownType: string): string {
        const widthMap: Record<string, string> = {
            stage: "w-42",
            accelerator: "w-40",
            campaign: "w-60",
            detector: "w-32",
        };
        return widthMap[dropdownType] || "w-auto";
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
        getBadgeColor,
        getBadgeItems,
        getWidthClass,
        formatFieldName,
        copyToClipboard,
        formatTimestamp,
        formatSizeInGiB,
        isStatusField,
        getStatusBadgeColor,
        getStatusFields,
    };
}
