<template>
    <div
        class="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800"
    >
        <!-- Dataset Controls -->
        <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
            <!-- Selection controls -->
            <div class="flex items-center gap-2">
                <UCheckbox
                    :model-value="allEntitiesSelected"
                    :disabled="datasets.length === 0"
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
                Download ({{ selectedCount }})
            </UButton>

            <div class="h-6 w-px bg-gray-300 dark:bg-gray-600" />

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
                    class="w-48"
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

                <!-- Batch size control -->
                <div class="flex items-center gap-1 text-sm">
                    <UTooltip text="Number of items to load at once. Range: 20-100" placement="top">
                        <span>Load:</span>
                    </UTooltip>
                    <UInput
                        :model-value="pageSize"
                        type="number"
                        min="20"
                        max="100"
                        size="xs"
                        class="w-16"
                        @update:model-value="$emit('updatePageSize', Number($event))"
                        @change="$emit('handlePageSizeChange')"
                    />
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { Dataset } from "~/types/dataset";

interface Props {
    datasets: Dataset[];
    allEntitiesSelected: boolean;
    selectedCount: number;
    isDownloading: boolean;
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
        e: "toggleSelectAll" | "downloadSelected" | "toggleAllMetadata" | "toggleSortOrder" | "handlePageSizeChange",
    ): void;
    (e: "updateSortBy", value: string): void;
    (e: "updatePageSize", value: number): void;
}

defineProps<Props>();
defineEmits<Emits>();
</script>
