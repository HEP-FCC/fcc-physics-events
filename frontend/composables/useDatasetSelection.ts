import { ref, reactive, shallowReactive, computed } from "vue";
import type { Dataset, SelectionState, MetadataEditState } from "~/types/dataset";

/**
 * Dataset selection and metadata management composable
 * Handles dataset selection, metadata expansion, and download functionality
 */
export function useDatasetSelection() {
    const { apiClient, apiAvailable } = useApiClient();
    const { createDatasetDownloadFilename, downloadAsJsonFile } = useUtils();

    // Dataset selection and UI expansion state
    const selectionState = reactive<SelectionState>({
        selectedDatasets: new Set<number>(),
        expandedMetadata: new Set<number>(),
        isDownloading: false,
    });

    // Force reactivity triggers for Set changes
    const selectedDatasetsVersion = ref(0);
    const expandedMetadataVersion = ref(0);

    // Metadata editing state - per-dataset editing context
    const metadataEditState = shallowReactive<Record<number, MetadataEditState>>({});

    // Computed properties for better reactivity
    const selectedCount = computed(() => {
        void selectedDatasetsVersion.value; // Force reactivity
        return selectionState.selectedDatasets.size;
    });

    const expandedMetadataList = computed(() => {
        void expandedMetadataVersion.value; // Force reactivity
        return Array.from(selectionState.expandedMetadata);
    });

    const selectedDatasetsList = computed(() => {
        void selectedDatasetsVersion.value; // Force reactivity
        return Array.from(selectionState.selectedDatasets);
    });

    function getAllDatasetsSelected(datasets: Dataset[]) {
        // Access the reactive version to trigger re-computation
        void selectedDatasetsVersion.value;
        const currentDatasetIds = datasets.map((dataset) => dataset.dataset_id);
        return currentDatasetIds.length > 0 && currentDatasetIds.every((id) => selectionState.selectedDatasets.has(id));
    }

    function getAllMetadataExpanded(datasets: Dataset[]) {
        // Access the reactive version to trigger re-computation
        void expandedMetadataVersion.value;
        const currentDatasetIds = datasets.map((dataset) => dataset.dataset_id);
        return currentDatasetIds.length > 0 && currentDatasetIds.every((id) => selectionState.expandedMetadata.has(id));
    }

    /**
     * Toggle individual dataset selection
     */
    function toggleDatasetSelection(datasetId: number): void {
        if (selectionState.selectedDatasets.has(datasetId)) {
            selectionState.selectedDatasets.delete(datasetId);
        } else {
            selectionState.selectedDatasets.add(datasetId);
        }
        selectedDatasetsVersion.value++;
    }

    /**
     * Toggle select all datasets on current page
     */
    function toggleSelectAll(datasets: Dataset[]): void {
        const currentDatasetIds = datasets.map((d) => d.dataset_id);
        const allSelected = currentDatasetIds.every((id) => selectionState.selectedDatasets.has(id));

        if (allSelected) {
            currentDatasetIds.forEach((id) => selectionState.selectedDatasets.delete(id));
        } else {
            currentDatasetIds.forEach((id) => selectionState.selectedDatasets.add(id));
        }
        selectedDatasetsVersion.value++;
    }

    /**
     * Toggle metadata expansion for a specific dataset
     */
    function toggleMetadata(datasetId: number): void {
        if (selectionState.expandedMetadata.has(datasetId)) {
            selectionState.expandedMetadata.delete(datasetId);
        } else {
            selectionState.expandedMetadata.add(datasetId);
        }
        expandedMetadataVersion.value++;
    }

    /**
     * Toggle all metadata expansions
     */
    function toggleAllMetadata(datasets: Dataset[]): void {
        const currentDatasetIds = datasets.map((dataset) => dataset.dataset_id);
        const allExpanded =
            currentDatasetIds.length > 0 && currentDatasetIds.every((id) => selectionState.expandedMetadata.has(id));

        if (allExpanded) {
            currentDatasetIds.forEach((id) => selectionState.expandedMetadata.delete(id));
        } else {
            currentDatasetIds.forEach((id) => selectionState.expandedMetadata.add(id));
        }
        expandedMetadataVersion.value++;
    }

    /**
     * Clear all metadata expansions
     */
    function clearMetadataExpansions(): void {
        selectionState.expandedMetadata.clear();
        expandedMetadataVersion.value++;
    }

    /**
     * Check if dataset is selected
     */
    function isDatasetSelected(datasetId: number): boolean {
        // Access the reactive version to trigger re-computation
        void selectedDatasetsVersion.value;
        return selectionState.selectedDatasets.has(datasetId);
    }

    /**
     * Check if metadata is expanded for dataset
     */
    function isMetadataExpanded(datasetId: number): boolean {
        // Access the reactive version to trigger re-computation
        void expandedMetadataVersion.value;
        return selectionState.expandedMetadata.has(datasetId);
    }

    /**
     * Download selected datasets as JSON file
     */
    async function downloadSelectedDatasets(): Promise<void> {
        const selectedDatasetIds = Array.from(selectionState.selectedDatasets);
        if (selectedDatasetIds.length === 0) {
            return;
        }

        selectionState.isDownloading = true;
        try {
            const datasetsToDownload = await apiClient.downloadDatasetsByIds(selectedDatasetIds);

            if (datasetsToDownload.length > 0) {
                const filename = createDatasetDownloadFilename(datasetsToDownload.length);
                downloadAsJsonFile(datasetsToDownload, filename);
            }
        } catch (error) {
            console.error("Failed to download datasets:", error);
        } finally {
            selectionState.isDownloading = false;
        }
    }

    /**
     * Handle row click for metadata toggle
     */
    function handleRowClick(event: MouseEvent, datasetId: number): void {
        // Don't trigger row click if text is being selected
        const selection = window.getSelection();
        if (selection && selection.toString().length > 0) {
            return;
        }

        // Don't trigger row click for interactive elements
        const target = event.target as HTMLElement;
        if (target.closest("button, a, input")) {
            return;
        }

        toggleMetadata(datasetId);
    }

    /**
     * Enter edit mode for dataset metadata
     */
    function enterEditMode(datasetId: number, metadata: Record<string, unknown>): void {
        metadataEditState[datasetId] = {
            isEditing: true,
            json: JSON.stringify(metadata, null, 2),
        };
    }

    /**
     * Cancel metadata editing
     */
    function cancelEdit(datasetId: number): void {
        if (Object.prototype.hasOwnProperty.call(metadataEditState, datasetId)) {
            // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
            delete metadataEditState[datasetId];
        }
    }

    /**
     * Save metadata changes
     */
    async function saveMetadataChanges(
        datasetId: number,
        datasets: Dataset[],
        updateDataset: (index: number, dataset: Dataset) => void,
        editedJson?: string,
    ): Promise<void> {
        const editState = metadataEditState[datasetId];
        if (!editState) return;

        const toast = useToast();
        // const { isAuthenticated, login } = useAuth();

        // // Check if user is authenticated
        // if (!isAuthenticated.value) {
        //     toast.add({
        //         title: "Authentication Required",
        //         description: "Please login to save dataset metadata.",
        //         color: "warning",
        //     });

        //     // Trigger login
        //     login();
        //     return;
        // }

        try {
            // Use the edited JSON if provided, otherwise fall back to the edit state JSON
            const jsonToSave = editedJson || editState.json;
            const parsedMetadata = JSON.parse(jsonToSave);

            // Call the backend API to save metadata with session-based authentication
            await apiClient.updateDataset(datasetId, parsedMetadata);

            toast.add({
                title: "Success",
                description: "Dataset metadata updated successfully.",
                color: "success",
            });

            // Update the dataset in the local state
            const datasetIndex = datasets.findIndex((d) => d.dataset_id === datasetId);
            if (datasetIndex !== -1) {
                updateDataset(datasetIndex, {
                    ...datasets[datasetIndex],
                    metadata: parsedMetadata,
                });
            }

            // Exit edit mode
            if (Object.prototype.hasOwnProperty.call(metadataEditState, datasetId)) {
                // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
                delete metadataEditState[datasetId];
            }
        } catch (error: unknown) {
            if (apiAvailable.value) {
                // Check if it's an authentication error
                if (error instanceof Error && error.message.includes("401")) {
                    toast.add({
                        title: "Authentication Required",
                        description: "Your session has expired. Please login again.",
                        color: "warning",
                    });
                    // login();
                    return;
                }

                const errorMessage =
                    error instanceof Error
                        ? error.message
                        : "An unknown error occurred. Please check the JSON format and try again.";
                toast.add({
                    title: "Error Saving Metadata",
                    description: errorMessage,
                    color: "error",
                });
                console.error("Failed to save metadata:", error);
            }
        }
    }

    /**
     * Calculate textarea rows for metadata editing
     */
    function getTextareaRows(datasetId: number): number {
        const editState = metadataEditState[datasetId];
        if (!editState) return 10;
        const lineCount = editState.json.split("\n").length;
        return Math.max(10, Math.min(lineCount + 1, 25));
    }

    return {
        // State
        selectionState,
        metadataEditState,

        // Computed
        selectedCount,
        expandedMetadataList,
        selectedDatasetsList,
        getAllDatasetsSelected,
        getAllMetadataExpanded,

        // Methods
        toggleDatasetSelection,
        toggleSelectAll,
        toggleMetadata,
        toggleAllMetadata,
        clearMetadataExpansions,
        isDatasetSelected,
        isMetadataExpanded,
        downloadSelectedDatasets,
        handleRowClick,
        enterEditMode,
        cancelEdit,
        saveMetadataChanges,
        getTextareaRows,
    };
}
