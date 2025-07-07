<script setup lang="ts">
import { computed, ref } from "vue";
import type { Dataset } from "../types/dataset";
import { getApiClient } from "~/composables/getApiClient";

defineOptions({
    name: "DatasetMetadata",
});

const props = defineProps<{
    dataset: Dataset;
}>();

const emit = defineEmits(["dataset-updated"]);

const isEditing = ref(false);
const metadataJson = ref("");
const apiClient = getApiClient();
const toast = useToast();

// Field classification constants
const LONG_STRING_FIELDS = ["path", "software-stack", "description", "url", "command"];
const EXCLUDED_FIELDS = new Set([
    "dataset-name",
    "detector_name",
    "stage_name",
    "campaign_name",
    "accelerator_name",
    "dataset_id",
    "description",
    "comment",
]);
const FIELD_DISPLAY_ORDER = ["software-stack", "path"];

// Determine grid layout for description and comment sections
const gridClass = computed(() => {
    const hasDescription = !!props.dataset.metadata.description;
    const hasComment = !!props.dataset.metadata.comment;
    return hasDescription && hasComment ? "grid-cols-2" : "grid-cols-1";
});

// Calculate the number of rows needed for the textarea
const textareaRows = computed(() => {
    const lineCount = metadataJson.value.split("\n").length;
    return Math.max(10, Math.min(lineCount + 1, 25)); // Min 10 rows, max 25
});

function enterEditMode() {
    metadataJson.value = JSON.stringify(props.dataset.metadata, null, 2);
    isEditing.value = true;
}

function cancelEdit() {
    isEditing.value = false;
}

async function saveChanges() {
    try {
        const updatedMetadata = JSON.parse(metadataJson.value);
        await apiClient.updateDataset(props.dataset.dataset_id, updatedMetadata);
        toast.add({
            title: "Success",
            description: "Dataset metadata updated successfully.",
            color: "success",
        });
        isEditing.value = false;
        emit("dataset-updated");
    } catch (error) {
        toast.add({
            title: "Error",
            description: "Failed to update metadata. Please check the JSON format.",
            color: "error",
        });
        console.error("Failed to save metadata:", error);
    }
}

// Field type checking functions
function isLongStringField(key: string, value: unknown): boolean {
    if (typeof value !== "string") return false;
    return LONG_STRING_FIELDS.includes(key.toLowerCase()) || value.length > 50;
}

function isShortField(key: string, value: unknown): boolean {
    if (typeof value === "number" || typeof value === "boolean") return true;
    return typeof value === "string" && value.length <= 20;
}

function isSizeField(key: string): boolean {
    return key.toLowerCase() === "size";
}

function isVectorField(value: unknown): boolean {
    return (
        Array.isArray(value) &&
        value.length > 0 &&
        value.every((item) => ["number", "string", "boolean"].includes(typeof item))
    );
}

// Format byte values as GiB for size fields
function formatSizeInGiB(bytes: unknown): string {
    const bytesNumber = Number(bytes);
    if (isNaN(bytesNumber) || bytesNumber < 0) return "N/A";

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

function formatVectorPreview(value: unknown[]): { preview: string; needsFullRow: boolean } {
    const firstFive = value.slice(0, 5);
    const preview =
        firstFive
            .map((item) => {
                if (typeof item === "number") {
                    return Number.isInteger(item) ? item.toString() : item.toFixed(3);
                }
                return String(item);
            })
            .join(", ") + (value.length > 5 ? ", ..." : "");

    // Determine layout based on content complexity
    const avgFieldNameLength = 20;
    const lengthIndicatorLength = String(value.length).length + 3;
    const totalContentLength = avgFieldNameLength + preview.length + lengthIndicatorLength;
    const hasLongItems = firstFive.some((item) => String(item).length > 30);

    const needsFullRow = totalContentLength > 60 || hasLongItems || preview.length > 50;

    return { preview, needsFullRow };
}

// Sort and group metadata fields for consistent display
const sortedMetadata = computed(() => {
    const entries = Object.entries(props.dataset.metadata);
    const filteredEntries = entries.filter(([key]) => !EXCLUDED_FIELDS.has(key));

    const endFields: [string, unknown][] = [];
    const regularFields: [string, unknown][] = [];
    const vectorFields: [string, unknown][] = [];

    filteredEntries.forEach(([key, value]) => {
        if (FIELD_DISPLAY_ORDER.includes(key)) {
            endFields.push([key, value]);
        } else if (isVectorField(value)) {
            vectorFields.push([key, value]);
        } else {
            regularFields.push([key, value]);
        }
    });

    // Sort each group alphabetically
    regularFields.sort(([a], [b]) => a.localeCompare(b));

    // Sort vector fields by layout requirements, then alphabetically
    vectorFields.sort(([keyA, valueA], [keyB, valueB]) => {
        const previewA = formatVectorPreview(valueA as unknown[]);
        const previewB = formatVectorPreview(valueB as unknown[]);

        if (previewA.needsFullRow !== previewB.needsFullRow) {
            return previewA.needsFullRow ? 1 : -1;
        }
        return keyA.localeCompare(keyB);
    });

    // Sort end fields by defined order
    endFields.sort(([a], [b]) => FIELD_DISPLAY_ORDER.indexOf(a) - FIELD_DISPLAY_ORDER.indexOf(b));

    return [...regularFields, ...endFields, ...vectorFields];
});

// Get the first vector field for visual separation
const firstVectorKey = computed(() => {
    const vectors = sortedMetadata.value.filter(([, value]) => isVectorField(value));
    return vectors.length > 0 ? vectors[0][0] : null;
});
</script>

<template>
    <div class="border-t border-gray-200 bg-gray-50 cursor-default" @click.stop>
        <div class="p-4">
            <div v-if="isEditing" class="space-y-3">
                <textarea
                    v-model="metadataJson"
                    :rows="textareaRows"
                    class="w-full p-2 font-mono text-sm bg-white border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                ></textarea>
                <div class="flex justify-end gap-2">
                    <UButton icon="i-heroicons-x-mark" color="error" @click="cancelEdit">Cancel</UButton>
                    <UButton icon="i-heroicons-check" color="success" @click="saveChanges">Save</UButton>
                </div>
            </div>
            <div v-else class="space-y-3">
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
                    <UButton icon="i-heroicons-pencil" size="xs" @click="enterEditMode">Edit</UButton>
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