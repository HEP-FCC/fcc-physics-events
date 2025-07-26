<template>
    <div
        class="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800"
    >
        <!-- Entity Controls -->
        <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
            <!-- Selection controls -->
            <div class="flex items-center gap-2">
                <UCheckbox
                    :model-value="allEntitiesSelected"
                    :disabled="entities.length === 0"
                    @change="$emit('toggleSelectAll')"
                />
                <label class="text-sm font-medium cursor-pointer" @click="$emit('toggleSelectAll')">Select All</label>
            </div>

            <UButton
                icon="i-heroicons-arrow-down-tray"
                color="primary"
                variant="solid"
                size="sm"
                class="cursor-pointer"
                :disabled="selectedCount === 0"
                :loading="isDownloading"
                @click="$emit('downloadSelected')"
            >
                Selected ({{ selectedCount }})
            </UButton>

            <UButton
                icon="i-heroicons-arrow-down-tray"
                color="neutral"
                variant="solid"
                size="sm"
                class="cursor-pointer"
                :disabled="displayRange.total === 0"
                :loading="isDownloadingFiltered"
                @click="$emit('downloadFiltered')"
            >
                Filtered ({{ displayRange.total }})
            </UButton>

            <div class="h-6 w-px bg-gray-300 dark:bg-gray-600"></div>

            <UButton
                :icon="allMetadataExpanded ? 'i-heroicons-eye-slash' : 'i-heroicons-eye'"
                color="neutral"
                variant="outline"
                size="sm"
                class="cursor-pointer"
                @click="$emit('toggleAllMetadata')"
            >
                {{ allMetadataExpanded ? "Hide All Metadata" : "Show All Metadata" }}
            </UButton>

            <!-- Metadata Tags Dropdown -->
            <MetadataTagsDropdown :entities="entities" />

            <div class="h-6 w-px bg-gray-300 dark:bg-gray-600" />

            <!-- Sorting controls -->
            <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Sort by:</span>
                <USelectMenu
                    :model-value="sortBy"
                    :items="sortingFieldOptions"
                    :loading="sortLoading"
                    placeholder="Select field"
                    value-key="value"
                    :search-input="{ placeholder: 'Search fields...' }"
                    size="sm"
                    class="w-38"
                    @update:model-value="$emit('updateSortBy', $event)"
                />
                <UButton
                    :icon="sortOrder === 'asc' ? 'i-heroicons-bars-arrow-up' : 'i-heroicons-bars-arrow-down'"
                    color="neutral"
                    variant="outline"
                    size="sm"
                    class="cursor-pointer"
                    @click="$emit('toggleSortOrder')"
                />
            </div>
        </div>

        <!-- Results Summary -->
        <div class="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
            <!-- Left side: Results count and page size control -->
            <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
                <!-- Results count -->
                <div class="text-sm text-gray-600 dark:text-gray-300">
                    Showing
                    <strong class="text-gray-900 dark:text-white">
                        {{ displayRange.start }}-{{ displayRange.end }}
                    </strong>
                    of
                    <strong class="text-gray-900 dark:text-white">
                        {{ displayRange.total }}
                    </strong>
                </div>

                <div class="h-6 w-px bg-gray-300 dark:bg-gray-600" />

                <!-- Page size control -->
                <div class="flex items-center gap-1 text-sm">
                    <UTooltip text="Number of items to load per page. Range: 25-1000" placement="top">
                        <span>Page size:</span>
                    </UTooltip>
                    <UInput
                        :model-value="pageSize"
                        type="number"
                        min="25"
                        max="1000"
                        size="xs"
                        class="w-16"
                        placeholder="25"
                        @update:model-value="handlePageSizeInput"
                        @blur="handlePageSizeBlur"
                    />
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { Entity } from "~/types/entity";
import MetadataTagsDropdown from "./MetadataTagsDropdown.vue";

interface Props {
    entities: Entity[];
    allEntitiesSelected: boolean;
    selectedCount: number;
    isDownloading: boolean;
    isDownloadingFiltered: boolean;
    allMetadataExpanded: boolean;
    sortBy: string;
    sortOrder: "asc" | "desc";
    sortingFieldOptions: Array<{ label: string; value: string }>;
    sortLoading: boolean;
    displayRange: { start: number; end: number; total: number };
    pageSize: number;
}

interface Emits {
    (
        e:
            | "toggleSelectAll"
            | "downloadSelected"
            | "downloadFiltered"
            | "toggleAllMetadata"
            | "toggleSortOrder"
            | "handlePageSizeChange",
    ): void;
    (e: "updateSortBy", value: string): void;
    (e: "updatePageSize", value: number): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// Handle page size input to prevent unwanted "0" insertion
const handlePageSizeInput = (value: string | number) => {
    const numValue = typeof value === 'string' ? parseInt(value, 10) : value;
    
    // Only emit if we have a valid number
    if (!isNaN(numValue) && numValue > 0) {
        emit('updatePageSize', numValue);
    }
};

// Handle page size blur to ensure we have a valid value
const handlePageSizeBlur = (event: Event) => {
    const target = event.target as HTMLInputElement;
    const value = parseInt(target.value, 10);
    
    // If the input is empty or invalid, reset to current pageSize
    if (isNaN(value) || value < 25) {
        target.value = props.pageSize.toString();
    } else {
        // Clamp the value within bounds and apply it
        const clampedValue = Math.max(25, Math.min(1000, value));
        target.value = clampedValue.toString();
        emit('updatePageSize', clampedValue);
        emit('handlePageSizeChange');
    }
};
</script>
