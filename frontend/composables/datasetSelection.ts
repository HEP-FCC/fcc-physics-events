import { reactive, computed } from "vue";
import type { Dataset } from "~/types/dataset";

export interface SelectionState {
    selectedDatasets: Set<number>;
    expandedMetadata: Set<number>;
    isDownloading: boolean;
}

/**
 * Composable for managing dataset selection and metadata expansion.
 */
export function datasetSelection() {
    const selectionState = reactive<SelectionState>({
        selectedDatasets: new Set<number>(),
        expandedMetadata: new Set<number>(),
        isDownloading: false,
    });

    function toggleDatasetSelection(datasetId: number) {
        if (selectionState.selectedDatasets.has(datasetId)) {
            selectionState.selectedDatasets.delete(datasetId);
        } else {
            selectionState.selectedDatasets.add(datasetId);
        }
    }

    function toggleSelectAll(datasets: Dataset[]) {
        const currentDatasetIds = datasets.map((d) => d.dataset_id);
        const allSelected = currentDatasetIds.every((id) => selectionState.selectedDatasets.has(id));

        if (allSelected) {
            currentDatasetIds.forEach((id) => selectionState.selectedDatasets.delete(id));
        } else {
            currentDatasetIds.forEach((id) => selectionState.selectedDatasets.add(id));
        }
    }

    function toggleMetadata(datasetId: number) {
        if (selectionState.expandedMetadata.has(datasetId)) {
            selectionState.expandedMetadata.delete(datasetId);
        } else {
            selectionState.expandedMetadata.add(datasetId);
        }
    }

    function toggleAllMetadata(datasets: Dataset[]) {
        const currentDatasetIds = datasets.map((dataset) => dataset.dataset_id);
        const allExpanded =
            currentDatasetIds.length > 0 && currentDatasetIds.every((id) => selectionState.expandedMetadata.has(id));

        if (allExpanded) {
            currentDatasetIds.forEach((id) => selectionState.expandedMetadata.delete(id));
        } else {
            currentDatasetIds.forEach((id) => selectionState.expandedMetadata.add(id));
        }
    }

    function clearSelections() {
        selectionState.selectedDatasets.clear();
        selectionState.expandedMetadata.clear();
    }

    function clearMetadataExpansions() {
        selectionState.expandedMetadata.clear();
    }

    function isDatasetSelected(datasetId: number): boolean {
        return selectionState.selectedDatasets.has(datasetId);
    }

    function isMetadataExpanded(datasetId: number): boolean {
        return selectionState.expandedMetadata.has(datasetId);
    }

    // Computed properties
    const selectedCount = computed(() => selectionState.selectedDatasets.size);

    const allDatasetsSelected = computed(() => {
        return (datasets: Dataset[]) => {
            const currentDatasetIds = datasets.map((dataset) => dataset.dataset_id);
            return (
                currentDatasetIds.length > 0 && currentDatasetIds.every((id) => selectionState.selectedDatasets.has(id))
            );
        };
    });

    const allMetadataExpanded = computed(() => {
        return (datasets: Dataset[]) => {
            const currentDatasetIds = datasets.map((dataset) => dataset.dataset_id);
            return (
                currentDatasetIds.length > 0 && currentDatasetIds.every((id) => selectionState.expandedMetadata.has(id))
            );
        };
    });

    return {
        // State
        selectionState,

        // Computed
        selectedCount,
        allDatasetsSelected,
        allMetadataExpanded,

        // Methods
        toggleDatasetSelection,
        toggleSelectAll,
        toggleMetadata,
        toggleAllMetadata,
        clearSelections,
        clearMetadataExpansions,
        isDatasetSelected,
        isMetadataExpanded,
    };
}
