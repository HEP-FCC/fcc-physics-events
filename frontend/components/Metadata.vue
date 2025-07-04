<script setup lang="ts">
import { computed } from "vue";
import type { Dataset } from "../types/dataset";

defineOptions({
    name: "DatasetMetadata",
});

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

function isLongStringField(key: string, value: unknown): boolean {
    if (typeof value !== "string") return false;
    const longFields = ["path", "software-stack", "description", "url", "command"];
    return longFields.includes(key.toLowerCase()) || value.length > 50;
}

function isShortField(key: string, value: unknown): boolean {
    if (typeof value === "number" || typeof value === "boolean") return true;
    if (typeof value === "string" && value.length <= 20) return true;
    return false;
}

function isSizeField(key: string): boolean {
    return key.toLowerCase() === "size";
}

function formatSizeInGiB(bytes: unknown): string {
    const bytesNumber = Number(bytes);
    if (isNaN(bytesNumber) || bytesNumber < 0) {
        return "N/A";
    }
    const gigabytes = bytesNumber / (1024 * 1024 * 1024);
    return `${gigabytes.toFixed(2)} GiB`;
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
            hour12: false,
            timeZoneName: "short",
        });
    } catch {
        return timestamp;
    }
}

// Vector field detection and formatting functions
function isVectorField(value: unknown): boolean {
    if (!Array.isArray(value)) return false;
    if (value.length === 0) return false;

    // Check if all elements are numbers or strings
    return value.every((item) => typeof item === "number" || typeof item === "string" || typeof item === "boolean");
}

function formatVectorPreview(value: unknown[]): { preview: string; needsFullRow: boolean } {
    const firstFive = value.slice(0, 5);
    let preview = firstFive
        .map((item) => {
            if (typeof item === "number") {
                // Format numbers to avoid excessive decimals
                return Number.isInteger(item) ? item.toString() : item.toFixed(3);
            }
            return String(item);
        })
        .join(", ");

    // Add ellipsis if there are more elements
    if (value.length > 5) {
        preview += ", ...";
    }

    // Estimate display width - rough calculation
    const estimatedWidth = preview.length * 8; // ~8px per character
    const needsFullRow = estimatedWidth > 200 || firstFive.some((item) => String(item).length > 20);

    return { preview, needsFullRow };
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

    const endFields: [string, unknown][] = [];
    const remainingFields: [string, unknown][] = [];

    filteredEntries.forEach(([key, value]) => {
        if (endOrder.includes(key)) {
            endFields.push([key, value]);
        } else {
            remainingFields.push([key, value]);
        }
    });

    // --- START DEBUG VECTORS ---
    // This is temporary code to test vector display.
    const debugVectors: [string, unknown][] = [
        ["debug_short_numbers", [1, 2, 3, 4]],
        ["debug_long_numbers", [1.12345, 2.56789, 3.14159265, 4.2, 5.5, 6.8, 7.0, 8.1]],
        ["debug_short_strings", ["alpha", "beta", "gamma", "delta"]],
        [
            "debug_long_strings",
            [
                "a_very_long_string_that_will_definitely_need_to_wrap",
                "another_super_long_string_to_force_a_full_row_layout",
            ],
        ],
        ["debug_mixed_types", [1, "two", 3.14, true, "five", false]],
        ["debug_booleans", [true, false, true, true, false, true, false]],
        ["debug_very_long_vector", Array.from({ length: 150 }, (_, i) => i + 1)],
        ["debug_single_long_item_vector", ["this_is_one_very_long_string_item_in_an_array_to_check_wrapping"]],
    ];
    // --- END DEBUG VECTORS ---

    // Sort remaining fields alphabetically by key.
    remainingFields.sort(([a], [b]) => a.localeCompare(b));

    // Sort end fields by their defined order.
    endFields.sort(([a], [b]) => endOrder.indexOf(a) - endOrder.indexOf(b));

    return [...remainingFields, ...debugVectors, ...endFields];
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
                        <div class="bg-white rounded border px-2 py-1 text-sm text-gray-800">
                            <p class="whitespace-pre-wrap">{{ dataset.metadata.description }}</p>
                        </div>
                    </div>
                    <div v-if="dataset.metadata.comment" class="space-y-1">
                        <label class="text-sm font-medium text-gray-700">Comment</label>
                        <div class="bg-white rounded border px-2 py-1 text-sm text-gray-800">
                            <p class="whitespace-pre-wrap">{{ dataset.metadata.comment }}</p>
                        </div>
                    </div>
                </div>

                <template v-for="[key, value] in sortedMetadata" :key="key">
                    <div v-if="isLongStringField(key, value)" class="space-y-1">
                        <label class="text-sm font-medium text-gray-700 capitalize">
                            {{ formatFieldName(key) }}
                        </label>
                        <div class="bg-white rounded border p-2 text-xs text-gray-800">
                            <code class="break-all">{{ value }}</code>
                        </div>
                    </div>

                    <div v-else-if="isSizeField(key)" class="inline-block mr-3 mb-2">
                        <UBadge color="neutral" variant="soft" size="md">
                            <span class="font-medium">{{ formatFieldName(key) }}:</span>
                            <span class="ml-1 font-normal">{{ formatSizeInGiB(value) }}</span>
                        </UBadge>
                    </div>

                    <div v-else-if="isShortField(key, value)" class="inline-block mr-3 mb-2">
                        <UBadge color="neutral" variant="soft" size="md">
                            <span class="font-medium">{{ formatFieldName(key) }}:</span>
                            <span class="ml-1 font-normal">{{ value }}</span>
                        </UBadge>
                    </div>

                    <div v-else-if="isVectorField(value)" class="space-y-1">
                        <label class="text-sm font-medium text-gray-700 capitalize">
                            {{ formatFieldName(key) }}
                            <span class="text-gray-500 font-normal ml-1 normal-case"
                                >(len: {{ (value as unknown[]).length }})</span
                            >
                        </label>
                        <div class="bg-white rounded border px-2 py-1 text-sm text-gray-800">
                            <span class="break-all font-mono text-xs">
                                {{ formatVectorPreview(value as unknown[]).preview }}
                            </span>
                        </div>
                    </div>

                    <div v-else class="space-y-1">
                        <label class="text-sm font-medium text-gray-700 capitalize">
                            {{ formatFieldName(key) }}
                        </label>
                        <div class="bg-white rounded border px-2 py-1 text-sm text-gray-800">
                            <span>{{ value }}</span>
                        </div>
                    </div>
                </template>
            </div>
        </div>
    </div>
</template>
