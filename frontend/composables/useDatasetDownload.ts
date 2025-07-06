/**
 * Utility composable for handling file downloads
 */

/**
 * Creates a filename with timestamp for dataset downloads
 */
export function createDatasetDownloadFilename(datasetCount: number): string {
    const now = new Date();
    const timestamp = now
        .toISOString()
        .slice(0, 19)
        .replace(/[-T:]/g, (match) => (match === "T" ? "_" : "-"));
    return `fcc_physics_datasets-${datasetCount}-datasets-${timestamp}.json`;
}

/**
 * Downloads data as a JSON file to the user's browser
 */
export function downloadAsJsonFile(data: unknown, filename: string): void {
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
}

/**
 * Composable for handling dataset downloads with proper error handling
 */
export function useDatasetDownload() {
    async function downloadSelectedDatasets(
        selectedDatasetIds: number[],
        apiClient: { downloadDatasetsByIds: (ids: number[]) => Promise<unknown[]> },
        onLoadingChange: (isLoading: boolean) => void,
    ): Promise<boolean> {
        if (selectedDatasetIds.length === 0) {
            return false; // Let the calling component handle the validation message
        }

        onLoadingChange(true);
        try {
            const datasetsToDownload = await apiClient.downloadDatasetsByIds(selectedDatasetIds);

            if (datasetsToDownload.length > 0) {
                const filename = createDatasetDownloadFilename(datasetsToDownload.length);
                downloadAsJsonFile(datasetsToDownload, filename);
                return true;
            }
            return false;
        } catch (error) {
            console.error("Failed to download datasets:", error);
            return false; // Let the calling component handle the error message
        } finally {
            onLoadingChange(false);
        }
    }

    return {
        downloadSelectedDatasets,
        createDatasetDownloadFilename,
        downloadAsJsonFile,
    };
}
