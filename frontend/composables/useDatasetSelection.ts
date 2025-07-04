import { reactive, computed } from "vue";
import type { Dataset } from "~/types/dataset";

export interface SelectionState {
    selectedDatasets: Set<number>;
    expandedRows: Set<number>;
    isDownloading: boolean;
}

export function useDatasetSelection() {
    const selectionState = reactive<SelectionState>({
        selectedDatasets: new Set<number>(),
        expandedRows: new Set<number>(),
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
        if (selectionState.expandedRows.has(datasetId)) {
            selectionState.expandedRows.delete(datasetId);
        } else {
            selectionState.expandedRows.add(datasetId);
        }
    }

    function toggleAllMetadata(datasets: Dataset[]) {
        const currentDatasetIds = datasets.map((dataset) => dataset.dataset_id);
        const allExpanded =
            currentDatasetIds.length > 0 && currentDatasetIds.every((id) => selectionState.expandedRows.has(id));

        if (allExpanded) {
            currentDatasetIds.forEach((id) => selectionState.expandedRows.delete(id));
        } else {
            currentDatasetIds.forEach((id) => selectionState.expandedRows.add(id));
        }
    }

    function clearSelections() {
        selectionState.selectedDatasets.clear();
        selectionState.expandedRows.clear();
    }

    function clearMetadataExpansions() {
        selectionState.expandedRows.clear();
    }

    function isDatasetSelected(datasetId: number): boolean {
        return selectionState.selectedDatasets.has(datasetId);
    }

    function isMetadataExpanded(datasetId: number): boolean {
        return selectionState.expandedRows.has(datasetId);
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
            return currentDatasetIds.length > 0 && currentDatasetIds.every((id) => selectionState.expandedRows.has(id));
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
