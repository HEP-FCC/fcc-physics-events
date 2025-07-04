<template>
    <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
        <!-- Selection controls -->
        <div class="flex items-center gap-2">
            <UCheckbox
                :model-value="allSelected"
                :disabled="totalDatasets === 0"
                @change="$emit('toggle-select-all')"
            />
            <label class="text-sm font-medium cursor-pointer" @click="$emit('toggle-select-all')">Select All</label>
        </div>

        <UButton
            icon="i-heroicons-arrow-down-tray"
            color="primary"
            variant="solid"
            size="sm"
            :disabled="selectedCount === 0"
            :loading="isDownloading"
            class="cursor-pointer"
            @click="$emit('download-selected')"
        >
            Download ({{ selectedCount }})
        </UButton>

        <div class="h-6 w-px bg-gray-300 dark:bg-gray-600"/>

        <!-- Metadata toggle -->
        <UButton
            :icon="allMetadataExpanded ? 'i-heroicons-eye-slash' : 'i-heroicons-eye'"
            color="neutral"
            variant="outline"
            size="sm"
            class="cursor-pointer"
            @click="$emit('toggle-all-metadata')"
        >
            {{ allMetadataExpanded ? "Hide All" : "Show All" }}
        </UButton>

        <div class="h-6 w-px bg-gray-300 dark:bg-gray-600"/>

        <!-- Sorting controls -->
        <div class="flex items-center gap-2">
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Sort by:</span>
            <USelectMenu
                :model-value="sortBy"
                :items="sortingOptions"
                :loading="sortingLoading"
                placeholder="Select field"
                value-key="value"
                :search-input="{ placeholder: 'Search fields...' }"
                size="sm"
                class="w-48"
                @update:model-value="$emit('update:sort-by', $event)"
            />
            <UButton
                :icon="sortOrder === 'asc' ? 'i-heroicons-bars-arrow-up' : 'i-heroicons-bars-arrow-down'"
                color="neutral"
                variant="outline"
                size="sm"
                class="cursor-pointer"
                :aria-label="`Sort ${sortOrder === 'asc' ? 'ascending' : 'descending'}`"
                @click="$emit('toggle-sort-order')"
            />
        </div>

        <!-- View mode toggle -->
        <UButton
            :icon="infiniteScrollEnabled ? 'i-heroicons-arrows-up-down' : 'i-heroicons-document-duplicate'"
            color="neutral"
            variant="outline"
            size="sm"
            class="cursor-pointer"
            @click="$emit('toggle-mode')"
        >
            {{ infiniteScrollEnabled ? "Infinite Scroll" : "Pagination" }}
        </UButton>
    </div>
</template>

<script setup lang="ts">
import type { DatasetControlsProps, DatasetControlEvents } from "~/types/components";

defineProps<DatasetControlsProps>();
defineEmits<DatasetControlEvents>();
</script>
