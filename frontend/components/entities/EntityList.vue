<template>
    <div>
        <!-- Entity List -->
        <div class="space-y-1.5">
            <!-- Entity cards -->
            <UCard
                v-for="(entity, index) in entities"
                :key="getEntityId(entity)"
                :data-entity-card="index"
                :ui="{ body: 'sm:p-1.5' }"
                class="overflow-hidden select-text cursor-pointer root-p-0"
                @click="handleRowClick($event, getEntityId(entity))"
            >
                <div class="px-2">
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
                            </div>

                            <!-- Row 2: Badges and timestamps in one compact row -->
                            <div class="flex items-center justify-between gap-4 ml-6">
                                <!-- Left side: Entity badges -->
                                <div class="flex flex-wrap gap-1.5 flex-1">
                                    <template v-for="badge in getEntityBadges(entity, activeFilters)" :key="badge.key">
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
const { formatTimestamp, getPrimaryKeyValue } = useUtils();
const { getEntityBadges } = useEntityBadges();

// Helper function to get entity ID
function getEntityId(entity: Entity): number {
    return getPrimaryKeyValue(entity) || 0;
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
