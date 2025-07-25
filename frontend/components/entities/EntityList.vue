<template>
    <div>
        <!-- Entity List -->
        <div class="space-y-2">
            <!-- Entity cards -->
            <UCard
                v-for="(entity, index) in entities"
                :key="getEntityId(entity)"
                :data-entity-card="index"
                class="overflow-hidden select-text cursor-pointer"
                @click="handleRowClick($event, getEntityId(entity))"
            >
                <div class="px-2 py-1.5">
                    <div class="flex items-center justify-between gap-3">
                        <div class="flex-1 min-w-0">
                            <!-- Row 1: Entity name (full width) -->
                            <div class="flex items-center gap-2 mb-0.5">
                                <UCheckbox
                                    :model-value="isEntitySelected(getEntityId(entity))"
                                    class="flex-shrink-0"
                                    @click.stop
                                    @change="toggleEntitySelection(getEntityId(entity))"
                                />
                                <h3 class="text-base font-semibold text-gray-900 dark:text-gray-100 truncate flex-1">
                                    {{ entity.name }}
                                </h3>
                                <UBadge color="neutral" variant="soft" size="xs" class="flex-shrink-0">
                                    ID: {{ getEntityId(entity) }}
                                </UBadge>
                            </div>

                            <!-- Row 2: Badges and timestamps in one compact row -->
                            <div class="flex items-center justify-between gap-4 ml-6">
                                <!-- Left side: Entity badges -->
                                <div class="flex flex-wrap gap-1.5 flex-1">
                                    <template v-for="badge in getEntityBadges(entity)" :key="badge.key">
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
                                <div
                                    class="flex flex-col items-end text-xs text-gray-500 dark:text-gray-400 flex-shrink-0"
                                >
                                    <span v-if="entity.created_at">
                                        Created: {{ formatTimestamp(entity.created_at) }}
                                    </span>
                                    <span
                                        v-if="wasEntityEdited(entity)"
                                        class="text-orange-600 dark:text-orange-400"
                                        :title="
                                            entity.last_edited_at
                                                ? `Last edited: ${formatTimestamp(entity.last_edited_at)}`
                                                : ''
                                        "
                                    >
                                        Edited
                                    </span>
                                </div>
                            </div>
                        </div>

                        <UButton
                            :icon="
                                isMetadataExpanded(getEntityId(entity))
                                    ? 'i-heroicons-chevron-up'
                                    : 'i-heroicons-chevron-down'
                            "
                            color="neutral"
                            variant="ghost"
                            size="xs"
                            class="flex-shrink-0"
                            @click.stop="toggleMetadata(getEntityId(entity))"
                        />
                    </div>
                </div>

                <!-- Metadata component (inline) -->
                <div
                    v-if="isMetadataExpanded(getEntityId(entity))"
                    class="border-t border-gray-200 bg-gray-50 cursor-default"
                    @click.stop
                >
                    <EntityMetadata
                        :entity-id="getEntityId(entity)"
                        :metadata="entity.metadata || {}"
                        :edit-state="metadataEditState[getEntityId(entity)]"
                        @enter-edit="enterEditMode"
                        @cancel-edit="cancelEdit"
                        @save-metadata="saveMetadata"
                        @refresh-entity="refreshEntity"
                    />
                </div>
            </UCard>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { Entity, ScrollState, SortState, SearchState } from "~/types/entity";
import type { SelectionState, MetadataEditState } from "~/types/api";
import EntityMetadata from "./EntityMetadata.vue";

// Import schema utilities for dynamic entity handling

/**
 * Entity List Component
 * Handles entity display, selection, metadata expansion, and infinite scroll
 */

interface Props {
    entities: Entity[];
    scrollState: ScrollState;
    sortState: SortState;
    selectionState: SelectionState;
    searchState: SearchState;
    metadataEditState: Record<number, MetadataEditState>;
    infiniteScrollEnabled: boolean;
    sortingFieldOptions: Array<{ label: string; value: string }>;
    currentDisplayRange: { start: number; end: number; total: number };
    shouldShowLoadingIndicator: boolean;
    shouldShowCompletionMessage: boolean;
    activeFilters?: Record<string, string>;
}

interface Emits {
    (e: "toggleEntitySelection" | "toggleMetadata" | "cancelEdit", entityId: number): void;
    (e: "saveMetadata", entityId: number, editedJson?: string): void;
    (e: "enterEditMode", entityId: number, metadata: Record<string, unknown>): void;
    (e: "refreshEntity", entityId: number): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// Composables
const { formatTimestamp, getStatusFields, formatFieldName, getPrimaryKeyValue } = useUtils();
const { getNavigationItem } = useNavigationConfig();

// Helper function to get entity ID
function getEntityId(entity: Entity): number {
    return getPrimaryKeyValue(entity) || 0;
}

// Create a reactive function to get badge items for an entity
function getEntityBadges(entity: Entity) {
    // Generate navigation badges for any field ending with '_name' that has a value
    const navigationBadges = Object.entries(entity)
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
                filterKey: key, // Store the original key for filter comparison
            };
        })
        .filter((badge) => {
            // Filter out badges that match currently active filters
            // activeFilters format: { "type_name": "value" }
            const activeFilterValue = props.activeFilters?.[badge.filterKey];
            return !activeFilterValue || activeFilterValue !== badge.value;
        });

    // Add status badges from metadata (these are always shown as they're not navigation filters)
    const statusBadges = getStatusFields(entity.metadata || {}).map((statusField) => ({
        key: statusField.key ? `status_${String(statusField.key)}` : "status_unknown", // Ensure key is always a valid string
        label: String(statusField.label || "Unknown"),
        value: String(statusField.value || ""),
        color: statusField.color || "neutral",
    }));

    return [...navigationBadges, ...statusBadges];
}

// Helper function to check if entity was actually edited
function wasEntityEdited(entity: Entity): boolean {
    if (!entity.last_edited_at || !entity.created_at) return false;

    // Ensure we have valid date strings
    if (typeof entity.last_edited_at !== "string" || typeof entity.created_at !== "string") return false;

    // Parse dates and compare timestamps
    const created = new Date(entity.created_at).getTime();
    const edited = new Date(entity.last_edited_at).getTime();

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

function refreshEntity(entityId: number): void {
    emit("refreshEntity", entityId);
}

function isEntitySelected(entityId: number): boolean {
    return props.selectionState.selectedEntities.has(entityId);
}

function isMetadataExpanded(entityId: number): boolean {
    return props.selectionState.expandedMetadata.has(entityId);
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
