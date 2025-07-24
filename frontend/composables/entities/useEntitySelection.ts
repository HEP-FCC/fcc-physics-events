// Auto-imported: ref, reactive, shallowReactive, computed
import type { Entity, SelectionState, MetadataEditState } from "~/types/api";
// Auto-imported: getPrimaryKeyValue, extractEntityIds

/**
 * Generic entity selection and metadata management composable
 * Handles entity selection, metadata expansion, and download functionality
 * Works with any entity type (books, products, etc.)
 */
export function useEntitySelection() {
    const { downloadEntitiesByIds } = useTypedApiClient();

    // Check API availability
    const apiAvailable = computed(() => {
        const config = useRuntimeConfig();
        return !!(config.public.apiBaseUrl || "http://localhost:8000");
    });

    const { createEntityDownloadFilename, downloadAsJsonFile } = useUtils();

    // Entity selection and UI expansion state
    const selectionState = reactive<SelectionState>({
        selectedIds: new Set<number>(),
        selectedEntities: new Set<number>(),
        expandedMetadata: new Set<number>(),
        selectAll: false,
        isIndeterminate: false,
        isDownloading: false,
    });

    // Force reactivity triggers for Set changes
    const selectedEntitiesVersion = ref(0);
    const expandedMetadataVersion = ref(0);

    // Metadata editing state - per-entity editing context
    const metadataEditState = shallowReactive<Record<number, MetadataEditState>>({});

    // Computed properties for better reactivity
    const selectedCount = computed(() => {
        void selectedEntitiesVersion.value; // Force reactivity
        return selectionState.selectedEntities.size;
    });

    const expandedMetadataList = computed(() => {
        void expandedMetadataVersion.value; // Force reactivity
        return Array.from(selectionState.expandedMetadata);
    });

    const selectedEntityList = computed(() => {
        void selectedEntitiesVersion.value; // Force reactivity
        return Array.from(selectionState.selectedEntities);
    });

    function getAllEntitiesSelected(entities: Entity[]) {
        if (entities.length === 0) return false;

        const currentEntityIds = extractEntityIds(entities);
        return (
            currentEntityIds.length > 0 &&
            currentEntityIds.every((id: number) => selectionState.selectedEntities.has(id))
        );
    }
    function getAllMetadataExpanded(entities: Entity[]) {
        // Access the reactive version to trigger re-computation
        void expandedMetadataVersion.value;
        const currentEntityIds = extractEntityIds(entities);
        return (
            currentEntityIds.length > 0 &&
            currentEntityIds.every((id: number) => selectionState.expandedMetadata.has(id))
        );
    }

    /**
     * Toggle individual entity selection
     */
    function toggleEntitySelection(entityIdOrData: number | Entity): void {
        const entityId = typeof entityIdOrData === "number" ? entityIdOrData : getPrimaryKeyValue(entityIdOrData);

        if (entityId === null) return;

        if (selectionState.selectedEntities.has(entityId)) {
            selectionState.selectedEntities.delete(entityId);
        } else {
            selectionState.selectedEntities.add(entityId);
        }
        selectedEntitiesVersion.value++;
    }

    /**
     * Toggle select all entities on current page
     */
    function toggleSelectAll(entities: Entity[]): void {
        const currentEntityIds = extractEntityIds(entities);
        const allSelected = currentEntityIds.every((id: number) => selectionState.selectedEntities.has(id));

        if (allSelected) {
            currentEntityIds.forEach((id: number) => selectionState.selectedEntities.delete(id));
        } else {
            currentEntityIds.forEach((id: number) => selectionState.selectedEntities.add(id));
        }
        selectedEntitiesVersion.value++;
    }

    /**
     * Toggle metadata expansion for a specific entity
     */
    function toggleMetadata(entityIdOrData: number | Entity): void {
        const entityId = typeof entityIdOrData === "number" ? entityIdOrData : getPrimaryKeyValue(entityIdOrData);

        if (entityId === null) return;

        if (selectionState.expandedMetadata.has(entityId)) {
            selectionState.expandedMetadata.delete(entityId);
        } else {
            selectionState.expandedMetadata.add(entityId);
        }
        expandedMetadataVersion.value++;
    }

    /**
     * Toggle all metadata expansions
     */
    function toggleAllMetadata(entities: Entity[]): void {
        const currentEntityIds = extractEntityIds(entities);
        const allExpanded =
            currentEntityIds.length > 0 &&
            currentEntityIds.every((id: number) => selectionState.expandedMetadata.has(id));

        if (allExpanded) {
            currentEntityIds.forEach((id: number) => selectionState.expandedMetadata.delete(id));
        } else {
            currentEntityIds.forEach((id: number) => selectionState.expandedMetadata.add(id));
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
     * Check if entity is selected
     */
    function isEntitySelected(entityId: number): boolean {
        // Access the reactive version to trigger re-computation
        void selectedEntitiesVersion.value;
        return selectionState.selectedEntities.has(entityId);
    }

    /**
     * Check if metadata is expanded for entity
     */
    function isMetadataExpanded(entityId: number): boolean {
        // Force reactivity check
        void selectedEntitiesVersion.value;
        return selectionState.expandedMetadata.has(entityId);
    }
    /**
     * Download selected entities as JSON file
     */
    async function downloadSelectedEntities(): Promise<void> {
        const selectedEntityIds = Array.from(selectionState.selectedEntities);
        if (selectedEntityIds.length === 0) {
            return;
        }

        selectionState.isDownloading = true;
        try {
            const entitiesToDownload = await downloadEntitiesByIds(selectedEntityIds);

            if (entitiesToDownload.length > 0) {
                const filename = createEntityDownloadFilename(entitiesToDownload.length);
                downloadAsJsonFile(entitiesToDownload, filename);
            }
        } catch (error) {
            console.error("Failed to download entities:", error);
        } finally {
            selectionState.isDownloading = false;
        }
    }

    /**
     * Handle row click for metadata toggle
     */
    function handleRowClick(event: MouseEvent, entityId: number): void {
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

        toggleMetadata(entityId);
    }

    /**
     * Enter edit mode for entity metadata
     */
    function enterEditMode(entityId: number, metadata: Record<string, unknown>): void {
        metadataEditState[entityId] = {
            isEditing: true,
            editingEntityId: entityId,
            editingData: {},
            hasChanges: false,
            json: JSON.stringify(metadata, null, 2),
            editedJson: JSON.stringify(metadata, null, 2),
            originalMetadata: metadata,
        };
    }

    /**
     * Cancel metadata editing
     */
    function cancelEdit(entityId: number): void {
        if (Object.prototype.hasOwnProperty.call(metadataEditState, entityId)) {
            metadataEditState[entityId].isEditing = false;
            // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
            delete metadataEditState[entityId];
        }
    }

    /**
     * Save metadata changes
     */
    async function saveMetadataChanges(
        entityId: number,
        entities: Entity[],
        updateEntity: (index: number, entity: Entity) => void,
        editedJson?: string,
    ): Promise<void> {
        const editState = metadataEditState[entityId];
        if (!editState) return;

        const toast = useToast();
        const { isAuthenticated, login } = useAuth();

        // Check if user is authenticated
        if (!isAuthenticated.value) {
            toast.add({
                title: "Authentication Required",
                description: "Please login to save entity metadata.",
                color: "warning",
            });

            // Trigger login
            login();
            return;
        }

        try {
            // Use the edited JSON if provided, otherwise fall back to the edit state JSON
            const jsonToSave = editedJson || editState.editedJson;
            const parsedMetadata = JSON.parse(jsonToSave);

            // Call the backend API to save metadata with cookie-based authentication
            const { updateEntity } = useTypedApiClient();
            await updateEntity(entityId, parsedMetadata);

            toast.add({
                title: "Success",
                description: "Entity metadata updated successfully.",
                color: "success",
            });

            // Update the entity in the local state
            const entityIndex = entities.findIndex((entity: Entity) => getPrimaryKeyValue(entity) === entityId);
            if (entityIndex !== -1) {
                updateEntity(entityIndex, {
                    ...entities[entityIndex],
                    dataset_id: entityId,
                    metadata: parsedMetadata,
                });
            }

            // Exit edit mode
            if (Object.prototype.hasOwnProperty.call(metadataEditState, entityId)) {
                // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
                delete metadataEditState[entityId];
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
                    login();
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
    function getTextareaRows(entityId: number): number {
        const editState = metadataEditState[entityId];
        if (!editState) return 10;
        const lineCount = editState.editedJson.split("\n").length;
        return Math.max(10, Math.min(lineCount + 1, 25));
    }

    /**
     * Get selected entities as Entity objects
     * Helper for bulk operations
     */
    function getSelectedEntitiesAsObjects(allEntities: Entity[]): Entity[] {
        return allEntities.filter((entity) => {
            const id = getPrimaryKeyValue(entity);
            return id && selectionState.selectedEntities.has(id);
        });
    }

    /**
     * Clear all selections
     */
    function clearAllSelections(): void {
        selectionState.selectedEntities.clear();
        selectionState.expandedMetadata.clear();
        selectedEntitiesVersion.value++;
        expandedMetadataVersion.value++;
    }

    /**
     * Select entities by IDs
     */
    function selectEntitiesByIds(entityIds: number[]): void {
        entityIds.forEach((id) => selectionState.selectedEntities.add(id));
        selectedEntitiesVersion.value++;
    }

    return {
        // State
        selectionState,
        metadataEditState,

        // Computed
        selectedCount,
        expandedMetadataList,
        selectedEntityList,
        getAllEntitiesSelected,
        getAllMetadataExpanded,

        // Methods
        toggleEntitySelection,
        toggleSelectAll,
        toggleMetadata,
        toggleAllMetadata,
        clearMetadataExpansions,
        isEntitySelected,
        isMetadataExpanded,
        downloadSelectedEntities,
        handleRowClick,
        enterEditMode,
        cancelEdit,
        saveMetadataChanges,
        getTextareaRows,

        // New helper methods
        getSelectedEntitiesAsObjects,
        clearAllSelections,
        selectEntitiesByIds,
    };
}
