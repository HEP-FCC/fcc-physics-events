<script setup lang="ts">
import { computed } from "vue";
import type { Dataset } from "../types/dataset";

defineOptions({
    name: "DatasetMetadata",
});

const props = defineProps<{
    dataset: Dataset;
}>();

// Determine grid layout for description and comment sections
const gridClass = computed(() => {
    const hasDescription = !!props.dataset.metadata.description;
    const hasComment = !!props.dataset.metadata.comment;
    if (hasDescription && hasComment) {
        return "grid-cols-2";
    }
    return "grid-cols-1";
});

// Check if field value should be displayed as a long string field
function isLongStringField(key: string, value: unknown): boolean {
    if (typeof value !== "string") return false;
    const longFields = ["path", "software-stack", "description", "url", "command"];
    return longFields.includes(key.toLowerCase()) || value.length > 50;
}

// Check if field value should be displayed as a compact badge
function isShortField(key: string, value: unknown): boolean {
    if (typeof value === "number" || typeof value === "boolean") return true;
    if (typeof value === "string" && value.length <= 20) return true;
    return false;
}

function isSizeField(key: string): boolean {
    return key.toLowerCase() === "size";
}

// Format byte values as GiB for size fields
function formatSizeInGiB(bytes: unknown): string {
    const bytesNumber = Number(bytes);
    if (isNaN(bytesNumber) || bytesNumber < 0) {
        return "N/A";
    }
    const gigabytes = bytesNumber / (1024 * 1024 * 1024);
    return `${gigabytes.toFixed(2)} GiB`;
}

// Convert field names to human-readable format
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

    // More intelligent width calculation for badge layout
    // Badge has fixed padding, field name, preview, and length indicator
    // Typical badge uses: "FieldName: preview (length)" format
    const fieldNameLength = 20; // Rough estimate for average field name including formatting
    const lengthIndicatorLength = String(value.length).length + 3; // " (123)" format
    const totalBadgeContent = fieldNameLength + preview.length + lengthIndicatorLength;

    // Consider individual item lengths - if any item in the preview is very long, use full row
    const hasLongItems = firstFive.some((item) => String(item).length > 30);

    // Use full row if:
    // 1. Total badge content would be longer than ~60 characters (comfortable badge width)
    // 2. Any individual item is too long (> 30 chars)
    // 3. Preview itself is quite long (> 50 chars) indicating complex data
    const needsFullRow = totalBadgeContent > 60 || hasLongItems || preview.length > 50;

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
    const nonVectorFields: [string, unknown][] = [];
    const vectorFields: [string, unknown][] = [];

    filteredEntries.forEach(([key, value]) => {
        if (endOrder.includes(key)) {
            endFields.push([key, value]);
        } else if (isVectorField(value)) {
            vectorFields.push([key, value]);
        } else {
            nonVectorFields.push([key, value]);
        }
    });

    // Sort non-vector fields alphabetically by key.
    nonVectorFields.sort(([a], [b]) => a.localeCompare(b));

    // Sort vector fields by display requirements (short ones first, then long ones) and then alphabetically
    vectorFields.sort(([keyA, valueA], [keyB, valueB]) => {
        const previewA = formatVectorPreview(valueA as unknown[]);
        const previewB = formatVectorPreview(valueB as unknown[]);

        // First sort by display type: short vectors before long vectors
        if (previewA.needsFullRow !== previewB.needsFullRow) {
            return previewA.needsFullRow ? 1 : -1;
        }

        // Then sort alphabetically within each group
        return keyA.localeCompare(keyB);
    });

    // Sort end fields by their defined order.
    endFields.sort(([a], [b]) => endOrder.indexOf(a) - endOrder.indexOf(b));

    return [...nonVectorFields, ...endFields, ...vectorFields];
});

// Get the first vector field key to add visual separation
const firstVectorKey = computed(() => {
    const vectors = sortedMetadata.value.filter(([, value]) => isVectorField(value));
    return vectors.length > 0 ? vectors[0][0] : null;
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
                    <!-- Add visual separator before first vector field -->
                    <div v-if="key === firstVectorKey" class="clear-both w-full" />

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

                    <!-- Vector fields - use same visual format, inline for short vectors, full row for long vectors -->
                    <div
                        v-else-if="isVectorField(value)"
                        :class="
                            formatVectorPreview(value as unknown[]).needsFullRow
                                ? 'w-full space-y-1'
                                : 'inline-block mr-3 mb-2 space-y-1'
                        "
                    >
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
