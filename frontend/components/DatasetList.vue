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

        <!-- Loading states and load more controls -->
        <div v-if="shouldShowLoadingIndicator" class="flex justify-center py-8">
            <div class="flex items-center space-x-3 text-sm text-gray-600 dark:text-gray-400">
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500" />
                <span>Loading more results...</span>
            </div>
        </div>

        <div v-else-if="shouldShowLoadMoreButton" class="flex justify-center py-6">
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

        <div v-else-if="shouldShowCompletionMessage" class="flex justify-center py-6">
            <div class="text-center text-sm text-gray-500 dark:text-gray-400">
                <UIcon name="i-heroicons-check-circle" class="inline mr-1" />
                All {{ totalDatasets }} results loaded
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { DatasetListProps, DatasetSelectionEvents, PaginationEvents } from "~/types/components";

const props = defineProps<DatasetListProps>();
defineEmits<DatasetSelectionEvents & PaginationEvents>();

// Computed properties for loading state management
const shouldShowLoadingIndicator = computed(() => {
    return props.isLoadingMore && props.infiniteScrollEnabled && props.canAutoLoad;
});

const shouldShowLoadMoreButton = computed(() => {
    return props.hasMore && !props.isLoadingMore && !props.infiniteScrollEnabled;
});

const shouldShowCompletionMessage = computed(() => {
    return !props.hasMore && props.datasets.length > 0 && props.totalDatasets > 0;
});
</script>
