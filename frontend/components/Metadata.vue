<script setup lang="ts">
import { computed } from "vue";
import type { Event } from "../types/event";

const props = defineProps<{
    event: Event;
}>();


// Computed property to determine the grid layout for description and comment.
const gridClass = computed(() => {
    const hasDescription = !!props.event.metadata.description;
    const hasComment = !!props.event.metadata.comment;
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

function formatFieldName(key: string): string {
    return key.replace(/[-_]/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
}

// Sort and group metadata fields for a consistent and logical display order.
const sortedMetadata = computed(() => {
    const entries = Object.entries(props.event.metadata);

    // Fields that are already displayed in the main event row and should be excluded here.
    const mainDisplayFields = new Set([
        "process-name",
        "detector_name",
        "framework_name",
        "campaign_name",
        "accelerator_name",
        "process_id",
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
                <div v-if="event.metadata.description || event.metadata.comment" class="grid gap-3" :class="gridClass">
                    <div v-if="event.metadata.description" class="space-y-1">
                        <label class="text-sm font-medium text-gray-700">Description</label>
                        <div class="bg-white rounded border px-2 py-1">
                            <p class="text-sm text-gray-800 whitespace-pre-wrap">{{ event.metadata.description }}</p>
                        </div>
                    </div>
                    <div v-if="event.metadata.comment" class="space-y-1">
                        <label class="text-sm font-medium text-gray-700">Comment</label>
                        <div class="bg-white rounded border px-2 py-1">
                            <p class="text-sm text-gray-800 whitespace-pre-wrap">{{ event.metadata.comment }}</p>
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

                    <div v-else-if="isShortField(key, value)" class="inline-block mr-3 mb-2">
                        <UBadge color="gray" variant="soft" size="md">
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
