<template>
    <div class="bg-gray-50 dark:bg-gray-800 rounded border-t border-gray-200 dark:border-gray-700">
        <!-- Editing Mode -->
        <div v-if="editState?.isEditing" class="p-6">
            <div class="flex items-center justify-between mb-4">
                <div>
                    <h4 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Edit Metadata</h4>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        Modify the JSON metadata for this {{ mainTableDisplayName.toLowerCase().slice(0, -1) }}
                    </p>
                </div>
                <div class="flex gap-2">
                    <UButton
                        icon="i-heroicons-check"
                        color="primary"
                        variant="solid"
                        size="sm"
                        :disabled="!isAuthenticated"
                        @click="saveMetadata"
                    >
                        {{ isAuthenticated ? "Save Changes" : "Login Required" }}
                    </UButton>
                    <UButton icon="i-heroicons-x-mark" color="neutral" variant="outline" size="sm" @click="cancelEdit">
                        Cancel
                    </UButton>
                </div>

                <!-- Authentication notice -->
                <div
                    v-if="!isAuthenticated"
                    class="text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 px-2 py-1 rounded border border-amber-200 dark:border-amber-800"
                >
                    <UIcon name="i-heroicons-exclamation-triangle" class="w-3 h-3 inline mr-1" />
                    Authentication required to save metadata changes
                </div>
            </div>

            <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                <UTextarea
                    v-model="localEditJson"
                    :rows="getTextareaRows()"
                    placeholder="Edit metadata JSON..."
                    resize
                    class="font-mono text-sm w-full"
                    autofocus
                />
                <div class="flex items-center justify-between mt-3 text-xs text-gray-500 dark:text-gray-400">
                    <span>{{ getJsonStats(localEditJson) }}</span>
                    <div class="flex items-center gap-2">
                        <UButton icon="i-heroicons-arrow-path" variant="ghost" size="xs" @click="formatJson">
                            Format JSON
                        </UButton>
                        <UButton
                            icon="i-heroicons-clipboard"
                            variant="ghost"
                            size="xs"
                            @click="copyToClipboard(localEditJson)"
                        >
                            Copy
                        </UButton>
                    </div>
                </div>
            </div>
        </div>

        <!-- Display Mode -->
        <div v-else>
            <!-- Header -->
            <div class="flex items-center justify-between px-2 py-1 border-b border-gray-200 dark:border-gray-700">
                <div>
                    <h4 class="text-xs font-medium text-gray-900 dark:text-gray-100">
                        Metadata ({{ visibleFieldCount }} fields)
                    </h4>
                </div>
                <UButton icon="i-heroicons-pencil" color="neutral" variant="ghost" size="xs" @click="enterEditMode">
                    Edit
                </UButton>
            </div>
            <!-- Compact Content -->
            <div class="p-2">
                <!-- Special Fields Section (Comments & Descriptions) - Side by Side -->
                <div v-if="getSpecialFields(props.metadata).length > 0" class="mb-2">
                    <div class="grid grid-cols-12 gap-2">
                        <div
                            v-for="[key, value] in getSpecialFields(props.metadata)"
                            :key="key"
                            :class="getSpecialFieldSpanClass(value)"
                            class="group relative rounded border border-indigo-200 dark:border-indigo-700 bg-indigo-100/60 dark:bg-indigo-950/50 hover:bg-indigo-200/70 dark:hover:bg-indigo-900/60 transition-colors duration-200 shadow-sm p-2"
                        >
                            <!-- Compact special field content -->
                            <div class="flex items-start gap-1.5">
                                <!-- Smaller icon -->
                                <div
                                    class="flex-shrink-0 w-4 h-4 rounded bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center"
                                >
                                    <span class="text-indigo-600 dark:text-indigo-400 text-[10px]">
                                        {{ getSpecialFieldIcon(key) }}
                                    </span>
                                </div>

                                <!-- Content -->
                                <div class="flex-1 min-w-0">
                                    <h6 class="text-xs font-semibold text-indigo-700 dark:text-indigo-300 mb-0.5">
                                        {{ getSpecialFieldTitle(key) }}
                                    </h6>
                                    <div class="flex items-center justify-between">
                                        <div class="text-xs text-gray-600 dark:text-gray-400 leading-tight flex-1">
                                            {{ String(value) }}
                                        </div>
                                        <div class="flex items-center gap-1 shrink-0 ml-2">
                                            <!-- Lock button for special fields (only show if authenticated) -->
                                            <UButton
                                                v-if="isAuthenticated"
                                                :icon="
                                                    isFieldLocked(key)
                                                        ? 'i-heroicons-lock-closed'
                                                        : 'i-heroicons-lock-open'
                                                "
                                                :color="isFieldLocked(key) ? 'warning' : 'neutral'"
                                                variant="ghost"
                                                size="xs"
                                                :padded="false"
                                                class="w-3 h-3 cursor-pointer opacity-70 hover:opacity-100 transition-all duration-200"
                                                :class="{
                                                    'hover:text-orange-500': !isFieldLocked(key),
                                                    'text-orange-600 hover:text-orange-700': isFieldLocked(key),
                                                }"
                                                :title="
                                                    isFieldLocked(key)
                                                        ? `Unlock ${getSpecialFieldTitle(key)}`
                                                        : `Lock ${getSpecialFieldTitle(key)}`
                                                "
                                                @click="toggleFieldLock(key)"
                                            />

                                            <!-- Copy button for special fields -->
                                            <UButton
                                                icon="i-heroicons-clipboard-document"
                                                color="neutral"
                                                variant="ghost"
                                                size="xs"
                                                :padded="false"
                                                class="w-3 h-3 cursor-pointer opacity-70 hover:opacity-100 hover:text-blue-500 transition-all duration-200"
                                                :title="`Copy ${getSpecialFieldTitle(key)} value`"
                                                @click="copyFieldValue(key, value)"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Regular Fields Grid Layout with Type-Based Row Breaks -->
                <div class="space-y-2">
                    <template
                        v-for="typeGroup in getFieldsByType(getRegularFieldsSorted(props.metadata))"
                        :key="typeGroup.type"
                    >
                        <!-- Type Row -->
                        <div class="grid grid-cols-12 gap-2 text-xs">
                            <template v-for="[key, value, type] in typeGroup.fields" :key="key">
                                <!-- Field card -->
                                <div
                                    :class="[getGridSpanClass(key, value, type), getFieldColorClass(type)]"
                                    class="group relative overflow-hidden rounded border shadow-sm"
                                >
                                    <!-- Background gradient -->
                                    <div
                                        class="absolute inset-0 bg-gradient-to-br opacity-5 group-hover:opacity-10 transition-opacity duration-200"
                                        :class="getGradientClass(type)"
                                    />

                                    <!-- Field Header with icon -->
                                    <div
                                        class="relative flex items-center justify-between px-2 py-1 border-b border-opacity-20"
                                        :class="getBorderClass(type)"
                                    >
                                        <div class="flex items-center gap-1 flex-1 min-w-0">
                                            <!-- Type icon -->
                                            <div
                                                class="flex-shrink-0 w-3 h-3 rounded-full flex items-center justify-center text-[9px]"
                                                :class="getIconClass(type)"
                                            >
                                                {{ getTypeIcon(type) }}
                                            </div>
                                            <span
                                                class="font-medium text-xs truncate"
                                                :class="getHeaderTextClass(type)"
                                                :title="formatFieldName(key)"
                                            >
                                                {{ formatFieldName(key) }}
                                            </span>
                                        </div>

                                        <!-- Vector length badge -->
                                        <UBadge
                                            v-if="type === 'vector'"
                                            color="primary"
                                            variant="soft"
                                            size="sm"
                                            class="shrink-0"
                                        >
                                            {{ (value as unknown[]).length }}
                                        </UBadge>
                                    </div>

                                    <!-- Field Value -->
                                    <div class="relative px-2 py-1.5 flex items-center justify-between min-h-[1.5rem]">
                                        <div
                                            :class="{
                                                'font-mono text-xs': type === 'vector',
                                                'text-center font-semibold': type === 'number' || type === 'boolean',
                                                'font-medium': type === 'shortString' || type === 'longString',
                                                truncate: type !== 'longString',
                                            }"
                                            class="flex-1 text-xs leading-tight"
                                            :title="getFieldValueTitle(key, value, type)"
                                        >
                                            <template v-if="type === 'vector'">
                                                {{ formatVectorPreview(value as unknown[]) }}
                                            </template>
                                            <template v-else-if="isSizeField(key) && type === 'number'">
                                                {{ formatSizeInGiB(getDisplayValue(value)) }}
                                            </template>
                                            <template v-else-if="type === 'number'">
                                                {{ formatShortValue(getDisplayValue(value)) }}
                                            </template>
                                            <template v-else>
                                                {{ formatShortValue(value) }}
                                            </template>
                                        </div>

                                        <!-- Action buttons -->
                                        <div class="flex items-center gap-1 shrink-0 ml-2">
                                            <!-- Lock button (only show if authenticated) -->
                                            <UButton
                                                v-if="isAuthenticated"
                                                :icon="
                                                    isFieldLocked(key)
                                                        ? 'i-heroicons-lock-closed'
                                                        : 'i-heroicons-lock-open'
                                                "
                                                :color="isFieldLocked(key) ? 'warning' : 'neutral'"
                                                variant="ghost"
                                                size="xs"
                                                :padded="false"
                                                class="w-4 h-4 cursor-pointer opacity-70 hover:opacity-100 transition-all duration-200"
                                                :class="{
                                                    'hover:text-orange-500': !isFieldLocked(key),
                                                    'text-orange-600 hover:text-orange-700': isFieldLocked(key),
                                                }"
                                                :title="
                                                    isFieldLocked(key)
                                                        ? `Unlock ${formatFieldName(key)}`
                                                        : `Lock ${formatFieldName(key)}`
                                                "
                                                @click="toggleFieldLock(key)"
                                            />

                                            <!-- Copy button -->
                                            <UButton
                                                icon="i-heroicons-clipboard-document"
                                                color="neutral"
                                                variant="ghost"
                                                size="xs"
                                                :padded="false"
                                                class="w-4 h-4 cursor-pointer opacity-70 hover:opacity-100 hover:text-blue-500 transition-all duration-200"
                                                :title="`Copy ${formatFieldName(key)} value`"
                                                @click="copyFieldValue(key, value)"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </template>
                        </div>
                    </template>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
// Auto-imported: ref, watch, watchEffect, computed
import type { MetadataEditState } from "~/types/api";
// Auto-imported: useAppConfiguration

/**
 * Entity Metadata Component
 * Displays and allows editing of entity metadata information
 * - Supports read-only view with syntax highlighting
 * - Provides edit mode with validation
 * - Works with any entity type dynamically
 */
interface Props {
    entityId?: number;
    metadata: Record<string, unknown>;
    editState?: MetadataEditState;
}

interface Emits {
    (e: "enterEdit", entityId: number, metadata: Record<string, unknown>): void;
    (e: "cancelEdit" | "saveMetadata", entityId: number, editedJson?: string): void;
    (e: "refreshEntity", entityId: number): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// Use the entityId directly
const actualEntityId = computed(() => props.entityId ?? 0);

// Composables
const { formatFieldName, formatSizeInGiB, copyToClipboard, isStatusField } = useUtils();
const { isAuthenticated } = useAuth();
const { mainTableDisplayName } = useAppConfiguration();

// Local reactive state for editing
const localEditJson = ref(props.editState?.json || "");

// Local reactive state for lock overrides (immediate UI updates)
const localLockStates = ref<Record<string, boolean>>({});

// Watch for changes to editState prop and update local state
watch(
    () => props.editState?.json,
    (newJson) => {
        if (newJson !== undefined) {
            localEditJson.value = newJson;
        }
    },
    { immediate: true },
);

// Watch for metadata changes and update edit JSON if in edit mode
watch(
    [() => props.metadata, () => localLockStates.value],
    () => {
        // Only update if we're currently in edit mode and localLockStates is initialized
        if (props.editState?.isEditing && localLockStates.value !== undefined) {
            const editableMetadata = getEditableMetadata();
            const newJson = JSON.stringify(editableMetadata, null, 2);
            localEditJson.value = newJson;
        }
    },
    { deep: true },
);

// Get filtered metadata without lock fields for editing
const getEditableMetadata = (): Record<string, unknown> => {
    const filtered: Record<string, unknown> = {};
    Object.entries(props.metadata).forEach(([key, value]) => {
        // Skip lock fields themselves
        if (isLockField(key)) {
            return;
        }

        // Skip fields that are currently locked
        if (isFieldLocked(key)) {
            return;
        }

        filtered[key] = value;
    });
    return filtered;
};

// Methods
const enterEditMode = (): void => {
    const editableMetadata = getEditableMetadata();
    emit("enterEdit", actualEntityId.value, editableMetadata);
};

const cancelEdit = (): void => {
    emit("cancelEdit", actualEntityId.value);
};

const saveMetadata = (): void => {
    emit("saveMetadata", actualEntityId.value, localEditJson.value);
};

const formatJson = (): void => {
    try {
        const parsed = JSON.parse(localEditJson.value);
        const formatted = JSON.stringify(parsed, null, 2);
        localEditJson.value = formatted;
    } catch (error) {
        console.error("Invalid JSON:", error);
        // Show user feedback for invalid JSON
        alert("Invalid JSON format. Please check your syntax.");
    }
};

// Lock-related functionality
const { updateMetadataLock } = useApiClient();
const toast = useToast();

// Initialize local lock states from props
watchEffect(() => {
    // Ensure all lock states are properly initialized
    Object.keys(props.metadata).forEach((key) => {
        if (key.includes("__lock__")) {
            const fieldName = key.replace("__", "").replace("__lock__", "");
            const metadataValue = !!props.metadata[key];
            localLockStates.value[fieldName] = metadataValue;
        }
    });
});

// Create a reactive function to check if fields are locked
const isFieldLocked = (fieldName: string): boolean => {
    // Always check local state first if it exists
    if (localLockStates.value && fieldName in localLockStates.value) {
        return localLockStates.value[fieldName];
    }

    // Fall back to props metadata if local state isn't available yet
    const lockFieldName = `__${fieldName}__lock__`;
    const isLocked = !!props.metadata[lockFieldName];

    // If we found a lock state in metadata but not in local state, sync it
    if (localLockStates.value && props.metadata[lockFieldName] !== undefined) {
        localLockStates.value[fieldName] = isLocked;
    }

    return isLocked;
};

const toggleFieldLock = async (fieldName: string): Promise<void> => {
    if (!isAuthenticated.value || !actualEntityId.value) {
        toast.add({
            title: "Authentication Required",
            description: "Please login to manage field locks.",
            color: "warning",
        });
        return;
    }

    const currentlyLocked = isFieldLocked(fieldName);
    const newLockState = !currentlyLocked;

    try {
        const response = await updateMetadataLock(actualEntityId.value, fieldName, newLockState);

        if (response.success) {
            // Only update local state after successful API response
            localLockStates.value[fieldName] = newLockState;

            toast.add({
                title: "Success",
                description: `Field "${formatFieldName(fieldName)}" ${
                    newLockState ? "locked" : "unlocked"
                } successfully.`,
                color: "success",
            });

            // Emit a refresh event so parent can update the entity data
            emit("refreshEntity", actualEntityId.value);
        } else {
            console.error("Lock operation failed:", response);
            toast.add({
                title: "Error",
                description: response.message || "Failed to update field lock.",
                color: "error",
            });
        }
    } catch (error) {
        console.error("Failed to toggle field lock:", error);
        toast.add({
            title: "Error",
            description: "Failed to update field lock. Please try again.",
            color: "error",
        });
    }
};

const getJsonStats = (json: string): string => {
    const lines = json.split("\n").length;
    const chars = json.length;
    return `${lines} lines, ${chars} characters`;
};

const getTextareaRows = (): number => {
    const lineCount = localEditJson.value.split("\n").length;
    return Math.max(15, Math.min(lineCount + 2, 35));
};

const isSizeField = (key: string): boolean => {
    return key.toLowerCase() === "size";
};

const isVectorField = (value: unknown): boolean => {
    return (
        Array.isArray(value) &&
        value.length > 0 &&
        value.every((item) => ["number", "string", "boolean"].includes(typeof item))
    );
};

const isLongString = (value: unknown): boolean => {
    return typeof value === "string" && value.length > 50;
};

// Check if a string value is actually a number
const isNumericString = (value: unknown): boolean => {
    if (typeof value !== "string") return false;
    const trimmed = value.trim();
    if (trimmed === "") return false;

    // Check for various number formats
    const number = Number(trimmed);
    return !isNaN(number) && isFinite(number);
};

// Parse numeric string to actual number
const parseNumericString = (value: string): number => {
    return Number(value.trim());
};

// Get the actual value for display (convert numeric strings to numbers)
const getDisplayValue = (value: unknown): unknown => {
    if (isNumericString(value)) {
        return parseNumericString(value as string);
    }
    return value;
};

const formatShortValue = (value: unknown): string => {
    if (typeof value === "number") {
        return Number.isInteger(value) ? value.toString() : value.toFixed(3);
    }
    if (typeof value === "boolean") {
        return value ? "Yes" : "No";
    }
    // Don't truncate strings - display them in full
    return String(value);
};

const formatVectorPreview = (value: unknown[]): string => {
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
    return preview;
};

// Visual styling functions for enhanced appearance
const getFieldColorClass = (type: string): string => {
    switch (type) {
        case "number":
            return "bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800";
        case "boolean":
            return "bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800";
        case "vector":
            return "bg-purple-50 dark:bg-purple-950 border-purple-200 dark:border-purple-800";
        case "longString":
            return "bg-amber-50 dark:bg-amber-950 border-amber-200 dark:border-amber-800";
        default: // shortString
            return "bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-700";
    }
};

const getGradientClass = (type: string): string => {
    switch (type) {
        case "number":
            return "from-blue-400 to-blue-600";
        case "boolean":
            return "from-green-400 to-green-600";
        case "vector":
            return "from-purple-400 to-purple-600";
        case "longString":
            return "from-amber-400 to-amber-600";
        default: // shortString
            return "from-slate-400 to-slate-600";
    }
};

const getBorderClass = (type: string): string => {
    switch (type) {
        case "number":
            return "border-blue-200 dark:border-blue-700";
        case "boolean":
            return "border-green-200 dark:border-green-700";
        case "vector":
            return "border-purple-200 dark:border-purple-700";
        case "longString":
            return "border-amber-200 dark:border-amber-700";
        default: // shortString
            return "border-slate-200 dark:border-slate-600";
    }
};

const getIconClass = (type: string): string => {
    switch (type) {
        case "number":
            return "bg-blue-200 dark:bg-blue-800 text-blue-700 dark:text-blue-300";
        case "boolean":
            return "bg-green-200 dark:bg-green-800 text-green-700 dark:text-green-300";
        case "vector":
            return "bg-purple-200 dark:bg-purple-800 text-purple-700 dark:text-purple-300";
        case "longString":
            return "bg-amber-200 dark:bg-amber-800 text-amber-700 dark:text-amber-300";
        default: // shortString
            return "bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300";
    }
};

const getTypeIcon = (type: string): string => {
    switch (type) {
        case "number":
            return "#";
        case "boolean":
            return "✓";
        case "vector":
            return "<>";
        case "longString":
            return "Aa";
        default: // shortString
            return "Aa";
    }
};

const getHeaderTextClass = (type: string): string => {
    switch (type) {
        case "number":
            return "text-blue-800 dark:text-blue-200";
        case "boolean":
            return "text-green-800 dark:text-green-200";
        case "vector":
            return "text-purple-800 dark:text-purple-200";
        case "longString":
            return "text-amber-800 dark:text-amber-200";
        default: // shortString
            return "text-slate-800 dark:text-slate-200";
    }
};

const getContentLength = (key: string, value: unknown, type: string): number => {
    const formattedKey = formatFieldName(key);
    let contentValue = "";

    switch (type) {
        case "vector":
            contentValue = formatVectorPreview(value as unknown[]);
            break;
        case "number": {
            const displayValue = getDisplayValue(value);
            contentValue = isSizeField(key) ? formatSizeInGiB(displayValue) : formatShortValue(displayValue);
            break;
        }
        default:
            contentValue = formatShortValue(value);
    }

    // Return total estimated character width
    return formattedKey.length + contentValue.length;
};

const getGridSpanClass = (key: string, value: unknown, type: string): string => {
    // Long strings always take full width
    if (type === "longString") {
        return "col-span-12";
    }

    const contentLength = getContentLength(key, value, type);

    // More compact grid spans based on content length and type (12-column grid)
    if (type === "number" || type === "boolean") {
        // Numbers and booleans are typically short - keep them very compact
        return contentLength <= 15 ? "col-span-2" : "col-span-3";
    } else if (type === "vector") {
        // Vectors need more space but be more aggressive with compacting
        return contentLength <= 30
            ? "col-span-3"
            : contentLength <= 50
            ? "col-span-4"
            : contentLength <= 70
            ? "col-span-6"
            : "col-span-12";
    } else {
        // Short strings - be more aggressive with space
        if (contentLength <= 15) return "col-span-2";
        if (contentLength <= 25) return "col-span-3";
        if (contentLength <= 40) return "col-span-4";
        if (contentLength <= 60) return "col-span-6";
        return "col-span-12";
    }
};

const getFieldValueTitle = (key: string, value: unknown, type: string): string => {
    // Return full value for tooltip on truncated fields
    if (type === "vector") {
        const fullArray = value as unknown[];
        return fullArray
            .map((item) =>
                typeof item === "number" ? (Number.isInteger(item) ? item.toString() : item.toFixed(3)) : String(item),
            )
            .join(", ");
    }

    if (type === "number") {
        const displayValue = getDisplayValue(value);
        if (isSizeField(key)) {
            return formatSizeInGiB(displayValue);
        }
        return formatShortValue(displayValue);
    }

    return formatShortValue(value);
};

// Special fields handling (comments and descriptions)
const isSpecialField = (key: string): boolean => {
    const normalizedKey = key.toLowerCase();
    return (
        normalizedKey.includes("comment") ||
        normalizedKey.includes("description") ||
        normalizedKey.includes("desc") ||
        normalizedKey === "summary" ||
        normalizedKey === "note" ||
        normalizedKey === "notes"
    );
};

// Lock fields handling (internal metadata fields)
const isLockField = (key: string): boolean => {
    return key.includes("__lock__");
};

// Get count of visible fields (excluding lock fields)
const visibleFieldCount = computed(() => {
    return Object.keys(props.metadata).filter((key) => !isLockField(key)).length;
});

const getSpecialFields = (metadata: Record<string, unknown>): [string, unknown][] => {
    return Object.entries(metadata)
        .filter(([key]) => isSpecialField(key) && !isLockField(key)) // Exclude lock fields from special fields too
        .sort(([a], [b]) => {
            // Prioritize certain field names
            const priorityOrder = ["description", "summary", "comment", "notes", "note"];
            const aPriority = priorityOrder.findIndex((p) => a.toLowerCase().includes(p));
            const bPriority = priorityOrder.findIndex((p) => b.toLowerCase().includes(p));

            if (aPriority !== -1 && bPriority !== -1) {
                return aPriority - bPriority;
            } else if (aPriority !== -1) {
                return -1;
            } else if (bPriority !== -1) {
                return 1;
            }
            return a.localeCompare(b);
        });
};

const getSpecialFieldIcon = (key: string): string => {
    const normalizedKey = key.toLowerCase();
    if (normalizedKey.includes("description") || normalizedKey.includes("desc")) return "📝";
    if (normalizedKey.includes("comment")) return "💬";
    return "💭";
};

const getSpecialFieldTitle = (key: string): string => {
    const normalizedKey = key.toLowerCase();
    if (normalizedKey.includes("description") || normalizedKey.includes("desc")) return "Description";
    if (normalizedKey.includes("comment")) return "Comment";
    return formatFieldName(key);
};

const getRegularFieldsSorted = (metadata: Record<string, unknown>): [string, unknown, string][] => {
    const fieldsWithTypes = Object.entries(metadata)
        .filter(([key]) => !isSpecialField(key) && !isLockField(key)) // Exclude special and lock fields (now includes status fields)
        .map(([key, value]): [string, unknown, string] => {
            if (isVectorField(value)) return [key, value, "vector"];
            if (typeof value === "number") return [key, value, "number"];
            if (typeof value === "boolean") return [key, value, "boolean"];
            if (isNumericString(value)) return [key, value, "number"]; // Treat numeric strings as numbers
            if (typeof value === "string" && isLongString(value)) return [key, value, "longString"];
            return [key, value, "shortString"];
        });

    // Define type order for consistent grouping
    const typeOrder = ["number", "boolean", "shortString", "vector", "longString"];

    return fieldsWithTypes.sort(([keyA, , typeA], [keyB, , typeB]) => {
        // First sort by type order
        const typeOrderA = typeOrder.indexOf(typeA);
        const typeOrderB = typeOrder.indexOf(typeB);

        if (typeOrderA !== typeOrderB) {
            return typeOrderA - typeOrderB;
        }

        // Then sort alphabetically within the same type
        return keyA.localeCompare(keyB);
    });
};

// Determine column span for special fields based on content length
const getSpecialFieldSpanClass = (value: unknown): string => {
    const stringValue = String(value);
    const isLong = stringValue.length > 60; // Reduced threshold for more compact layout
    return isLong ? "col-span-12" : "col-span-6";
};

// Group fields by type for row-based display
const getFieldsByType = (
    fields: [string, unknown, string][],
): Array<{ type: string; fields: [string, unknown, string][] }> => {
    const grouped = new Map<string, [string, unknown, string][]>();

    fields.forEach(([key, value, type]) => {
        if (!grouped.has(type)) {
            grouped.set(type, []);
        }
        grouped.get(type)!.push([key, value, type]);
    });

    // Convert to array and maintain type order
    const typeOrder = ["number", "boolean", "shortString", "vector", "longString"];
    return typeOrder
        .filter((type) => grouped.has(type))
        .map((type) => ({
            type,
            fields: grouped.get(type)!,
        }));
};

// Copy field value to clipboard with type handling
const copyFieldValue = async (key: string, value: unknown): Promise<void> => {
    try {
        let textToCopy: string;

        // Handle different types of values
        if (Array.isArray(value)) {
            // For arrays, copy as JSON
            textToCopy = JSON.stringify(value, null, 2);
        } else if (typeof value === "object" && value !== null) {
            // For objects, copy as JSON
            textToCopy = JSON.stringify(value, null, 2);
        } else {
            // For primitives, copy as string
            textToCopy = String(value);
        }

        await copyToClipboard(textToCopy);

        // Show success toast
        const toast = useToast();
        toast.add({
            title: "Value copied to clipboard",
            icon: "i-heroicons-clipboard-document-check",
        });
    } catch (error) {
        console.error("Failed to copy field value:", error);

        // Show error toast
        const toast = useToast();
        toast.add({
            title: "Failed to copy value",
            description: "Please try again",
            icon: "i-heroicons-exclamation-triangle",
            color: "error",
        });
    }
};
</script>
