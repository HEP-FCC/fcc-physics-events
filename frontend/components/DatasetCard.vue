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

                        <!-- Dynamic badges for stage, campaign, detector, accelerator -->
                        <div
                            v-for="badge in badgeItems"
                            :key="badge.key"
                            :class="badge.widthClass"
                            class="flex-shrink-0"
                        >
                            <UBadge v-if="badge.value" :color="badge.color" variant="subtle" size="md">
                                <span>{{ badge.label }}:</span>
                                <span class="ml-1">{{ badge.value }}</span>
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
                    @click.stop="$emit('toggle-metadata', dataset.dataset_id)"
                />
            </div>
        </div>

        <!-- Metadata component -->
        <Metadata v-if="isExpanded" :dataset="dataset" />
    </UCard>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { DatasetCardProps, DatasetSelectionEvents } from "~/types/components";

const props = defineProps<DatasetCardProps>();
const emit = defineEmits<DatasetSelectionEvents>();

// Badge configuration for dataset attributes
const badgeItems = computed(() => [
    {
        key: "stage",
        label: "Stage",
        value: props.dataset.stage_name,
        color: "success" as const,
        widthClass: "w-42",
    },
    {
        key: "campaign",
        label: "Campaign",
        value: props.dataset.campaign_name,
        color: "warning" as const,
        widthClass: "w-60",
    },
    {
        key: "detector",
        label: "Detector",
        value: props.dataset.detector_name,
        color: "info" as const,
        widthClass: "w-32",
    },
    {
        key: "accelerator",
        label: "Accelerator",
        value: props.dataset.accelerator_name,
        color: "secondary" as const,
        widthClass: "w-40",
    },
]);

function handleRowClick(event: MouseEvent) {
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

    emit("row-click", event, props.dataset.dataset_id);
}
</script>
