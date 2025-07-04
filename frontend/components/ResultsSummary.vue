<template>
    <div class="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <!-- Left side: Results count and page size control -->
        <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
            <!-- Results count -->
            <div class="text-sm text-gray-600 dark:text-gray-300">
                Showing
                <strong class="text-gray-900 dark:text-white"> {{ displayRange.start }}-{{ displayRange.end }} </strong>
                of
                <strong class="text-gray-900 dark:text-white">
                    {{ displayRange.total }}
                </strong>
            </div>

            <div class="h-6 w-px bg-gray-300 dark:bg-gray-600" />

            <!-- Page size control -->
            <div class="flex items-center gap-1 text-sm">
                <span>Per page:</span>
                <UInput
                    :model-value="pageSize"
                    type="number"
                    min="1"
                    max="100"
                    size="xs"
                    class="w-16"
                    @update:model-value="$emit('update:page-size', Number($event))"
                    @change="$emit('page-size-changed')"
                />
            </div>
        </div>
    </div>

    <!-- Pagination component (only in pagination mode) -->
    <div v-if="!infiniteScrollEnabled" class="flex justify-center mt-4 w-full">
        <UPagination
            :page="currentPage"
            :total="totalDatasets"
            :page-count="pageSize"
            size="sm"
            @update:page="$emit('update:page', $event)"
        />
    </div>
</template>

<script setup lang="ts">
import type { ResultsSummaryProps, PaginationEvents } from "~/types/components";

defineProps<ResultsSummaryProps>();
defineEmits<PaginationEvents>();
</script>
