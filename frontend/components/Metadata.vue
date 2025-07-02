<script setup lang="ts">
import { computed } from "vue";
import type { Dataset } from "../types/dataset";

const props = defineProps<{
    dataset: Dataset;
}>();

// Computed property to determine the grid layout for description and comment.
const gridClass = computed(() => {
    const hasDescription = !!props.dataset.metadata.description;
    const hasComment = !!props.dataset.metadata.comment;
    if (hasDescription && hasComment) {
        return "grid-cols-2";
    }
    return "grid-cols-1";
});

function isLongStringField(key: string, value: any): boolean {
    if (typeof value !== "string") return false;
    const longFields = ["path", "software-stack", "description", "url", "command"];
    return longFields.includes(key.toLowerCase()) || value.length > 50;
}

function isShortField(key: string, value: any): boolean {
    if (typeof value === "number" || typeof value === "boolean") return true;
    if (typeof value === "string" && value.length <= 20) return true;
    return false;
}

function isSizeField(key: string): boolean {
    return key.toLowerCase() === "size";
}

function formatSizeInGiB(bytes: any): string {
    const num = Number(bytes);
    if (isNaN(num) || num < 0) {
        return "N/A";
    }
    const gib = num / (1024 * 1024 * 1024);
    return `${gib.toFixed(2)} GiB`;
}

function formatFieldName(key: string): string {
    return key.replace(/[-_]/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
}

function formatTimestamp(timestamp: string): string {
    try {
        const date = new Date(timestamp);
        return date.toLocaleString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            timeZoneName: "short",
        });
    } catch (error) {
        return timestamp;
    }
}

// Sort and group metadata fields for a consistent and logical display order.
const sortedMetadata = computed(() => {
    const entries = Object.entries(props.dataset.metadata);

    // Fields that are already displayed in the main dataset row and should be excluded here.
    const mainDisplayFields = new Set([
        "dataset-name",
        "detector_name",
        "stage_name",
        "campaign_name",
        "accelerator_name",
        "dataset_id",
        "description",
        "comment",
    ]);
    const filteredEntries = entries.filter(([key]) => !mainDisplayFields.has(key));

    const endOrder = ["software-stack", "path"];

    const endFields: [string, any][] = [];
    const remainingFields: [string, any][] = [];

    filteredEntries.forEach(([key, value]) => {
        if (endOrder.includes(key)) {
            endFields.push([key, value]);
        } else {
            remainingFields.push([key, value]);
        }
    });

    // Sort remaining fields alphabetically by key.
    remainingFields.sort(([a], [b]) => a.localeCompare(b));

    // Sort end fields by their defined order.
    endFields.sort(([a], [b]) => endOrder.indexOf(a) - endOrder.indexOf(b));

    return [...remainingFields, ...endFields];
});
</script>

<template>
    <div class="border-t border-gray-200 bg-gray-50 cursor-default" @click.stop>
        <div class="p-4">
            <div class="space-y-3">
                <!-- Timestamp Information -->
                <div class="flex justify-between items-center text-xs text-gray-500 border-b border-gray-200 pb-2">
                    <div class="flex items-center gap-4">
                        <div class="flex items-center gap-1">
                            <UIcon name="i-heroicons-plus-circle" class="w-3 h-3" />
                            <span>Created:</span>
                            <span class="font-medium">{{ formatTimestamp(dataset.created_at) }}</span>
                        </div>
                        <div v-if="dataset.last_edited_at" class="flex items-center gap-1">
                            <UIcon name="i-heroicons-pencil-square" class="w-3 h-3" />
                            <span>Last edited:</span>
                            <span class="font-medium">{{ formatTimestamp(dataset.last_edited_at) }}</span>
                        </div>
                    </div>
                </div>

                <div
                    v-if="dataset.metadata.description || dataset.metadata.comment"
                    class="grid gap-3"
                    :class="gridClass"
                >
                    <div v-if="dataset.metadata.description" class="space-y-1">
                        <label class="text-sm font-medium text-gray-700">Description</label>
                        <div class="bg-white rounded border px-2 py-1">
                            <p class="text-sm text-gray-800 whitespace-pre-wrap">{{ dataset.metadata.description }}</p>
                        </div>
                    </div>
                    <div v-if="dataset.metadata.comment" class="space-y-1">
                        <label class="text-sm font-medium text-gray-700">Comment</label>
                        <div class="bg-white rounded border px-2 py-1">
                            <p class="text-sm text-gray-800 whitespace-pre-wrap">{{ dataset.metadata.comment }}</p>
                        </div>
                    </div>
                </div>

                <template v-for="[key, value] in sortedMetadata" :key="key">
                    <div v-if="isLongStringField(key, value)" class="space-y-1">
                        <label class="text-sm font-medium text-gray-700 capitalize">
                            {{ formatFieldName(key) }}
                        </label>
                        <div class="bg-white rounded border p-2">
                            <code class="text-xs text-gray-800 break-all">{{ value }}</code>
                        </div>
                    </div>

                    <div v-else-if="isSizeField(key)" class="inline-block mr-3 mb-2">
                        <UBadge color="neutral" variant="soft" size="md">
                            <span class="text-gray-600 font-medium text-sm">{{ formatFieldName(key) }}:</span>
                            <span class="ml-1 font-normal text-sm">{{ formatSizeInGiB(value) }}</span>
                        </UBadge>
                    </div>

                    <div v-else-if="isShortField(key, value)" class="inline-block mr-3 mb-2">
                        <UBadge color="neutral" variant="soft" size="md">
                            <span class="text-gray-600 font-medium text-sm">{{ formatFieldName(key) }}:</span>
                            <span class="ml-1 font-normal text-sm">{{ value }}</span>
                        </UBadge>
                    </div>

                    <div v-else class="space-y-1">
                        <label class="text-sm font-medium text-gray-700 capitalize">
                            {{ formatFieldName(key) }}
                        </label>
                        <div class="bg-white rounded border px-2 py-1">
                            <span class="text-sm text-gray-800">{{ value }}</span>
                        </div>
                    </div>
                </template>
            </div>
        </div>
    </div>
</template>
