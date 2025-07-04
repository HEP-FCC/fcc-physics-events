<template>
    <UCard :data-dataset-card="index" class="overflow-hidden select-text cursor-pointer" @click="handleRowClick">
        <div class="px-4 py-1">
            <div class="flex items-center justify-between gap-4">
                <div class="flex-1 min-w-0">
                    <div class="flex items-center">
                        <!-- Selection checkbox -->
                        <div class="flex-shrink-0 pr-4">
                            <UCheckbox
                                :model-value="isSelected"
                                @click.stop="$emit('toggle-selection', dataset.dataset_id)"
                            />
                        </div>

                        <!-- Dataset name -->
                        <div class="w-88 flex-shrink-0">
                            <h3 class="font-semibold text-base text-gray-900 dark:text-white">
                                {{ dataset.name }}
                            </h3>
                        </div>

                        <!-- Stage badge -->
                        <div class="w-42 flex-shrink-0">
                            <UBadge v-if="dataset.stage_name" color="success" variant="subtle" size="md">
                                <span>Stage:</span>
                                <span class="ml-1">{{ dataset.stage_name }}</span>
                            </UBadge>
                        </div>

                        <!-- Campaign badge -->
                        <div class="w-60 flex-shrink-0">
                            <UBadge v-if="dataset.campaign_name" color="warning" variant="subtle" size="md">
                                <span>Campaign:</span>
                                <span class="ml-1">{{ dataset.campaign_name }}</span>
                            </UBadge>
                        </div>

                        <!-- Detector badge -->
                        <div class="w-32 flex-shrink-0">
                            <UBadge v-if="dataset.detector_name" color="info" variant="subtle" size="md">
                                <span>Detector:</span>
                                <span class="ml-1">{{ dataset.detector_name }}</span>
                            </UBadge>
                        </div>

                        <!-- Accelerator badge -->
                        <div class="w-40 flex-shrink-0">
                            <UBadge v-if="dataset.accelerator_name" color="secondary" variant="subtle" size="md">
                                <span>Accelerator:</span>
                                <span class="ml-1">{{ dataset.accelerator_name }}</span>
                            </UBadge>
                        </div>
                    </div>
                </div>

                <!-- Expand/collapse button -->
                <UButton
                    :icon="isExpanded ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-down'"
                    color="primary"
                    variant="ghost"
                    size="md"
                    class="cursor-pointer"
                    :aria-label="`${isExpanded ? 'Hide' : 'Show'} metadata for ${dataset.name}`"
                    @click.stop="$emit('toggle-metadata', dataset.dataset_id)"
                />
            </div>
        </div>

        <!-- Metadata component -->
        <Metadata v-if="isExpanded" :dataset="dataset" />
    </UCard>
</template>

<script setup lang="ts">
import type { DatasetCardProps, DatasetSelectionEvents } from "~/types/components";

const props = defineProps<DatasetCardProps>();
const emit = defineEmits<DatasetSelectionEvents>();

function handleRowClick(event: MouseEvent) {
    // Don't trigger row click if text is being selected or a button was clicked
    const selection = window.getSelection();
    if (selection && selection.toString().length > 0) {
        return;
    }

    const target = event.target as HTMLElement;
    if (target.closest("button, a, input")) {
        return;
    }

    emit("row-click", event, props.dataset.dataset_id);
}
</script>
