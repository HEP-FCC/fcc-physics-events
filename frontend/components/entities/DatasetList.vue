<template>
    <div>
        <!-- Dataset List -->
        <div class="space-y-2">
            <!-- Dataset cards -->
            <UCard
                v-for="(dataset, index) in datasets"
                :key="getEntityId(dataset)"
                :data-dataset-card="index"
                class="overflow-hidden select-text cursor-pointer"
                @click="handleRowClick($event, getEntityId(dataset))"
            >
                <div class="px-2 py-1.5">
                    <div class="flex items-center justify-between gap-3">
                        <div class="flex-1 min-w-0">
                            <!-- Row 1: Dataset name (full width) -->
                            <div class="flex items-center gap-2 mb-0.5">
                                <UCheckbox
                                    :model-value="isEntitySelected(getEntityId(dataset))"
                                    class="flex-shrink-0"
                                    @click.stop
                                    @change="toggleEntitySelection(getEntityId(dataset))"
                                />
                                <h3 class="text-base font-semibold text-gray-900 dark:text-gray-100 truncate flex-1">
                                    {{ dataset.name }}
                                </h3>
                                <UBadge color="neutral" variant="soft" size="xs" class="flex-shrink-0">
                                    ID: {{ getEntityId(dataset) }}
                                </UBadge>
                            </div>

                            <!-- Row 2: Badges and timestamps in one compact row -->
                            <div class="flex items-center justify-between gap-4 ml-6">
                                <!-- Left side: Dataset badges -->
                                <div class="flex flex-wrap gap-1.5 flex-1">
                                    <template v-for="badge in getDatasetBadges(dataset)" :key="badge.key">
                                        <UBadge
                                            v-if="badge.value"
                                            :color="badge.color"
                                            :variant="
                                                badge.key && String(badge.key).startsWith('status_') ? 'soft' : 'subtle'
                                            "
                                            size="sm"
                                        >
                                            {{ badge.label }}: {{ badge.value }}
                                        </UBadge>
                                    </template>
                                </div>

                                <!-- Right side: Timestamps -->
                                <div class="flex gap-4 text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
                                    <span v-if="dataset.created_at"
                                        >Created: {{ formatTimestamp(dataset.created_at) }}</span
                                    >
                                    <span
                                        v-if="wasDatasetEdited(dataset)"
                                        class="text-amber-600 dark:text-amber-400 flex items-center gap-1 cursor-help"
                                        :title="
                                            dataset.last_edited_at
                                                ? `Last edited: ${formatTimestamp(dataset.last_edited_at)}`
                                                : 'Last edited date unknown'
                                        "
                                    >
                                        <span class="text-[10px]">✎</span>
                                        Edited
                                    </span>
                                </div>
                            </div>
                        </div>

                        <UButton
                            :icon="
                                isMetadataExpanded(getEntityId(dataset))
                                    ? 'i-heroicons-chevron-up'
                                    : 'i-heroicons-chevron-down'
                            "
                            color="neutral"
                            variant="ghost"
                            size="xs"
                            class="flex-shrink-0"
                            @click.stop="toggleMetadata(getEntityId(dataset))"
                        />
                    </div>
                </div>

                <!-- Metadata component (inline) -->
                <div
                    v-if="isMetadataExpanded(getEntityId(dataset))"
                    class="border-t border-gray-200 bg-gray-50 cursor-default"
                    @click.stop
                >
                    <DatasetMetadata
                        :entity-id="getEntityId(dataset)"
                        :metadata="dataset.metadata || {}"
                        :edit-state="metadataEditState[getEntityId(dataset)]"
                        @enter-edit="enterEditMode"
                        @cancel-edit="cancelEdit"
                        @save-metadata="saveMetadata"
                    />
                </div>
            </UCard>
        </div>
    </div>
</template>

<script setup lang="ts">
import type {
    Dataset,
    PaginationState,
    SortState,
    SelectionState,
    SearchState,
    MetadataEditState,
} from "~/types/dataset";
import { getPrimaryKeyField, getPrimaryKeyValue, getEntityType } from "~/composables/useSchemaUtils";
import DatasetMetadata from "./DatasetMetadata.vue";

// Import schema utilities for dynamic entity handling

/**
 * Dataset List Component
 * Handles dataset display, selection, metadata expansion, and infinite scroll
 */

interface Props {
    datasets: Dataset[];
    pagination: PaginationState;
    sortState: SortState;
    selectionState: SelectionState;
    searchState: SearchState;
    metadataEditState: Record<number, MetadataEditState>;
    infiniteScrollEnabled: boolean;
    sortingFieldOptions: Array<{ label: string; value: string }>;
    currentDisplayRange: { start: number; end: number; total: number };
    shouldShowLoadingIndicator: boolean;
    shouldShowCompletionMessage: boolean;
}

interface Emits {
    (e: "toggleEntitySelection" | "toggleMetadata" | "cancelEdit", entityId: number): void;
    (e: "saveMetadata", entityId: number, editedJson?: string): void;
    (e: "enterEditMode", entityId: number, metadata: Record<string, unknown>): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// Composables
const { formatTimestamp, getStatusFields, formatFieldName } = useUtils();
const { getNavigationItem, navigationConfig } = useNavigationConfig();

// Detect the primary key field dynamically
const primaryKeyField = computed(() => getPrimaryKeyField(props.datasets));

// Helper function to get entity ID
function getEntityId(entity: any): number {
    return getPrimaryKeyValue(entity) || 0;
}

// Create a reactive function to get badge items for a dataset
function getDatasetBadges(dataset: Dataset) {
    // Generate navigation badges for any field ending with '_name' that has a value
    const navigationBadges = Object.entries(dataset)
        .filter(([key, value]) => {
            return key.endsWith("_name") && value && typeof value === "string" && value.trim() !== "";
        })
        .map(([key, value]) => {
            const navType = key.replace("_name", "");

            // Try to get navigation config
            let config;
            try {
                config = getNavigationItem(navType);
            } catch {
                // Fallback config when navigation not loaded or type not found
                config = {
                    label: formatFieldName(navType),
                    badgeColor: "neutral" as const,
                };
            }

            return {
                key: navType ? String(navType) : "unknown", // Ensure key is always a valid string
                label: String(config?.label || formatFieldName(navType || "unknown")),
                value: String(value || ""),
                color: config?.badgeColor || "neutral",
            };
        });

    // Add status badges from metadata
    const statusBadges = getStatusFields(dataset.metadata || {}).map((statusField) => ({
        key: statusField.key ? `status_${String(statusField.key)}` : "status_unknown", // Ensure key is always a valid string
        label: String(statusField.label || "Unknown"),
        value: String(statusField.value || ""),
        color: statusField.color || "neutral",
    }));

    return [...navigationBadges, ...statusBadges];
}

// Helper function to check if dataset was actually edited
function wasDatasetEdited(dataset: Dataset): boolean {
    if (!dataset.last_edited_at || !dataset.created_at) return false;

    // Ensure we have valid date strings
    if (typeof dataset.last_edited_at !== "string" || typeof dataset.created_at !== "string") return false;

    // Parse dates and compare timestamps
    const created = new Date(dataset.created_at).getTime();
    const edited = new Date(dataset.last_edited_at).getTime();

    // Consider edited if there's more than 1 second difference (to account for minor timing differences)
    return Math.abs(edited - created) > 1000;
}

// Methods
function toggleEntitySelection(entityId: number): void {
    emit("toggleEntitySelection", entityId);
}

function toggleMetadata(entityId: number): void {
    emit("toggleMetadata", entityId);
}

function enterEditMode(entityId: number, metadata: Record<string, unknown>): void {
    emit("enterEditMode", entityId, metadata);
}

function cancelEdit(entityId: number): void {
    emit("cancelEdit", entityId);
}

function saveMetadata(entityId: number, editedJson?: string): void {
    emit("saveMetadata", entityId, editedJson);
}

function isEntitySelected(entityId: number): boolean {
    return props.selectionState.selectedEntities.has(entityId);
}

function isMetadataExpanded(datasetId: number): boolean {
    return props.selectionState.expandedMetadata.has(datasetId);
}

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
</script>
