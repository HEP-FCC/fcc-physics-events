<template>
    <div class="space-y-2">
        <!-- Dataset cards -->
        <DatasetCard
            v-for="(dataset, index) in datasets"
            :key="dataset.dataset_id"
            :dataset="dataset"
            :index="index"
            :is-selected="isDatasetSelected(dataset.dataset_id)"
            :is-expanded="isMetadataExpanded(dataset.dataset_id)"
            @toggle-selection="$emit('toggle-selection', $event)"
            @toggle-metadata="$emit('toggle-metadata', $event)"
            @row-click="(event, datasetId) => $emit('row-click', event, datasetId)"
        />

        <!-- Infinite scroll loading animation -->
        <div v-if="isLoadingMore && infiniteScrollEnabled" class="flex justify-center py-8">
            <div class="flex items-center space-x-3 text-sm text-gray-600 dark:text-gray-400">
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500" />
                <span>Loading more results...</span>
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500" />
            </div>
        </div>

        <!-- Manual load more button -->
        <div v-else-if="hasMore && infiniteScrollEnabled && !canAutoLoad" class="flex justify-center py-6">
            <UButton
                color="primary"
                variant="outline"
                size="lg"
                icon="i-heroicons-chevron-down"
                :loading="isLoadingMore"
                @click="$emit('load-more')"
            >
                Load More Results ({{ remainingResults }} remaining)
            </UButton>
        </div>

        <!-- End of results indicator -->
        <div v-else-if="!hasMore && datasets.length > 0 && infiniteScrollEnabled" class="flex justify-center py-6">
            <div class="text-center text-sm text-gray-500 dark:text-gray-400">
                <UIcon name="i-heroicons-check-circle" class="inline mr-1" />
                All {{ totalDatasets }} results loaded
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { DatasetListProps, DatasetSelectionEvents, PaginationEvents } from "~/types/components";

defineProps<DatasetListProps>();
defineEmits<DatasetSelectionEvents & PaginationEvents>();
</script>
