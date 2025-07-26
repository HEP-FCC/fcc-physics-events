<template>
    <!-- v-memo to prevent unnecessary re-renders when props haven't changed -->
    <div
        class="bg-gray-50 dark:bg-gray-800 rounded border-t border-gray-200 dark:border-gray-700"
        v-memo="[props.entityId, Object.keys(props.metadata).length, editState?.isEditing]"
    >
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
                <!-- Unified Fields Grid Layout -->
                <div v-if="getAllFieldsComputed.length > 0" class="space-y-2">
                    <!-- Group fields by display row priority -->
                    <template v-for="fieldGroup in getGroupedFieldsComputed" :key="fieldGroup.priority">
                        <div class="grid grid-cols-12 gap-2 text-xs">
                            <template v-for="field in fieldGroup.fields" :key="field.key">
                                <!-- Unified Field Card -->
                                <div
                                    :class="[getUnifiedGridSpanClass(field), getUnifiedFieldColorClass(field)]"
                                    class="group relative overflow-hidden rounded border transition-colors duration-200 shadow-sm"
                                >
                                    <!-- Background gradient (only for regular fields) -->
                                    <div
                                        v-if="field.category === 'regular'"
                                        class="absolute inset-0 bg-gradient-to-br opacity-5 group-hover:opacity-10 transition-opacity duration-200"
                                        :class="getUnifiedGradientClass(field)"
                                    />

                                    <!-- Unified Field Header -->
                                    <div
                                        class="relative flex items-center justify-between px-2 py-1 border-b border-opacity-20"
                                        :class="getUnifiedBorderClass(field)"
                                    >
                                        <div class="flex items-center gap-1.5 flex-1 min-w-0">
                                            <!-- Unified icon -->
                                            <div
                                                :class="[
                                                    getUnifiedIconContainerClass(field),
                                                    getUnifiedIconClass(field),
                                                ]"
                                                class="flex-shrink-0 flex items-center justify-center"
                                            >
                                                <span :class="getUnifiedIconTextClass(field)" class="text-[10px]">
                                                    {{ getUnifiedFieldIcon(field) }}
                                                </span>
                                            </div>
                                            <!-- Field title -->
                                            <span
                                                class="font-medium text-xs truncate"
                                                :class="getUnifiedHeaderTextClass(field)"
                                                :title="field.displayName"
                                            >
                                                {{ field.displayName }}
                                            </span>
                                        </div>

                                        <!-- Special badges/indicators -->
                                        <UBadge
                                            v-if="field.type === 'vector'"
                                            color="primary"
                                            variant="soft"
                                            size="sm"
                                            class="shrink-0"
                                        >
                                            {{ (field.value as unknown[]).length }}
                                        </UBadge>
                                    </div>

                                    <!-- Unified Field Value -->
                                    <div class="relative px-2 py-1.5 flex items-center justify-between min-h-[1.5rem]">
                                        <div
                                            :class="getUnifiedValueDisplayClass(field)"
                                            class="flex-1 text-xs leading-tight"
                                            :title="getUnifiedFieldValueTitle(field)"
                                        >
                                            {{ getUnifiedDisplayValue(field) }}
                                        </div>

                                        <!-- Action buttons -->
                                        <div class="flex items-center gap-1 shrink-0 ml-2">
                                            <!-- Lock indicator -->
                                            <UButton
                                                :icon="
                                                    isFieldLocked(field.key)
                                                        ? 'i-heroicons-lock-closed'
                                                        : 'i-heroicons-lock-open'
                                                "
                                                :color="isFieldLocked(field.key) ? 'warning' : 'neutral'"
                                                variant="ghost"
                                                size="xs"
                                                :padded="false"
                                                :disabled="!isAuthenticated"
                                                :class="[
                                                    getUnifiedLockButtonSize(field),
                                                    {
                                                        'cursor-pointer opacity-70 hover:opacity-100 hover:text-orange-500':
                                                            isAuthenticated && !isFieldLocked(field.key),
                                                        'cursor-pointer opacity-70 hover:opacity-100 text-orange-600 hover:text-orange-700':
                                                            isAuthenticated && isFieldLocked(field.key),
                                                        'cursor-not-allowed opacity-50': !isAuthenticated,
                                                    },
                                                ]"
                                                class="transition-all duration-200"
                                                :title="getUnifiedLockTitle(field)"
                                                @click="isAuthenticated ? toggleFieldLock(field.key) : undefined"
                                            />

                                            <!-- Copy button -->
                                            <UButton
                                                icon="i-heroicons-clipboard-document"
                                                color="neutral"
                                                variant="ghost"
                                                size="xs"
                                                :padded="false"
                                                :class="getUnifiedLockButtonSize(field)"
                                                class="cursor-pointer opacity-70 hover:opacity-100 hover:text-blue-500 transition-all duration-200"
                                                :title="`Copy ${field.displayName} value`"
                                                @click="copyFieldValue(field.key, field.value)"
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
// Auto-imported: ref, watch, watchEffect, computed, nextTick
import type { MetadataEditState } from "~/types/api";
// Auto-imported: useAppConfiguration

/**
 * Entity Metadata Component - SIMPLIFIED ARCHITECTURE
 *
 * This component has been refactored to reduce code duplication and template complexity
 * while maintaining the exact same visual appearance and functionality.
 *
 * KEY IMPROVEMENTS:
 * 1. UNIFIED FIELD PROCESSING: All field types (special, status, regular) are now processed
 *    through a single pipeline using the UnifiedField interface
 *
 * 2. CONSOLIDATED TEMPLATE: Replaced 3 separate rendering patterns with 1 unified loop
 *    - Reduces template code by ~70%
 *    - Eliminates duplication of field rendering logic
 *
 * 3. CENTRALIZED STYLING: Color schemes and styling functions are now unified
 *    - Single source of truth for all field colors/styles
 *    - Easier to maintain and extend
 *
 * 4. MAINTAINED FUNCTIONALITY: All features preserved:
 *    - Field locking/unlocking
 *    - Copy to clipboard
 *    - Edit mode with JSON validation
 *    - Responsive grid layout
 *    - Type-specific icons and formatting
 *
 * ARCHITECTURE:
 * - getAllFieldsComputed: Processes all metadata into UnifiedField objects
 * - getGroupedFieldsComputed: Groups fields by priority for visual separation
 * - getUnified*Class functions: Centralized styling with category-aware logic
 * - Single template loop handles all field types with conditional rendering
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

// Performance optimizations - applied universally to ALL entity metadata
// No longer using lazy loading - show all fields by default

// Composables
const { formatFieldName, formatSizeInGiB, copyToClipboard, isStatusField, getStatusBadgeColor } = useUtils();
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

// Optimized lock field handling with memoization
const lockedFieldsSet = computed(() => {
    const lockedFields = new Set<string>();

    // Process local state first (most up-to-date)
    if (localLockStates.value) {
        Object.entries(localLockStates.value).forEach(([fieldName, isLocked]) => {
            if (isLocked) {
                lockedFields.add(fieldName);
            }
        });
    }

    // Process metadata lock fields as fallback
    Object.keys(props.metadata).forEach((key) => {
        if (key.includes("__lock__")) {
            const fieldName = key.replace("__", "").replace("__lock__", "");
            const isLocked = !!props.metadata[key];

            // Only add if not already in local state
            if (!localLockStates.value || !(fieldName in localLockStates.value)) {
                if (isLocked) {
                    lockedFields.add(fieldName);
                }
                // Sync to local state
                if (localLockStates.value) {
                    localLockStates.value[fieldName] = isLocked;
                }
            }
        }
    });

    return lockedFields;
});

// Initialize local lock states from props (optimized)
watchEffect(() => {
    if (!localLockStates.value) return;

    // Only process lock fields once per metadata change
    const lockFields = Object.keys(props.metadata).filter((key) => key.includes("__lock__"));

    lockFields.forEach((key) => {
        const fieldName = key.replace("__", "").replace("__lock__", "");
        const metadataValue = !!props.metadata[key];

        // Only update if value actually changed
        if (localLockStates.value[fieldName] !== metadataValue) {
            localLockStates.value[fieldName] = metadataValue;
        }
    });
});

// Optimized lock checking - O(1) lookup instead of string operations
const isFieldLocked = (fieldName: string): boolean => {
    return lockedFieldsSet.value.has(fieldName);
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

// Get count of visible fields (excluding lock fields) - optimized
const visibleFieldCount = computed(() => {
    return getAllFieldsComputed.value.length;
});

// Memoized field processing to avoid expensive recalculations
const processedFields = computed(() => {
    const metadata = props.metadata;

    // Separate and process different field types
    const specialFields: [string, unknown][] = [];
    const statusFields: Array<{
        key: string;
        label: string;
        value: unknown;
        color: "success" | "warning" | "info" | "primary" | "secondary" | "error" | "neutral";
    }> = [];
    const regularFieldsWithTypes: [string, unknown, string][] = [];

    Object.entries(metadata).forEach(([key, value]) => {
        // Skip lock fields
        if (isLockField(key)) return;

        if (isSpecialField(key)) {
            specialFields.push([key, value]);
        } else if (isStatusField(key)) {
            statusFields.push({
                key,
                label: formatFieldName(key),
                value,
                color: getStatusBadgeColor(value),
            });
        } else {
            // Regular field - determine type
            let type: string;
            if (isVectorField(value)) type = "vector";
            else if (typeof value === "number") type = "number";
            else if (typeof value === "boolean") type = "boolean";
            else if (isNumericString(value)) type = "number"; // Treat numeric strings as numbers
            else if (typeof value === "string" && isLongString(value)) type = "longString";
            else type = "shortString";

            regularFieldsWithTypes.push([key, value, type]);
        }
    });

    // Sort special fields
    specialFields.sort(([a], [b]) => {
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

    // Sort status fields
    statusFields.sort((a, b) => a.label.localeCompare(b.label));

    // Sort regular fields
    const typeOrder = ["number", "boolean", "shortString", "vector", "longString"];
    regularFieldsWithTypes.sort(([keyA, , typeA], [keyB, , typeB]) => {
        const typeOrderA = typeOrder.indexOf(typeA);
        const typeOrderB = typeOrder.indexOf(typeB);

        if (typeOrderA !== typeOrderB) {
            return typeOrderA - typeOrderB;
        }
        return keyA.localeCompare(keyB);
    });

    // Group regular fields by type
    const groupedRegularFields = new Map<string, [string, unknown, string][]>();
    regularFieldsWithTypes.forEach(([key, value, type]) => {
        if (!groupedRegularFields.has(type)) {
            groupedRegularFields.set(type, []);
        }
        groupedRegularFields.get(type)!.push([key, value, type]);
    });

    const fieldsByType = typeOrder
        .filter((type) => groupedRegularFields.has(type))
        .map((type) => ({
            type,
            fields: groupedRegularFields.get(type)!,
        }));

    return {
        specialFields,
        statusFields,
        regularFieldsWithTypes,
        fieldsByType,
        visibleCount: specialFields.length + statusFields.length + regularFieldsWithTypes.length,
    };
});

// UNIFIED FIELD PROCESSING - Simplified approach to reduce code duplication
// Define unified field interface
interface UnifiedField {
    key: string;
    value: unknown;
    displayName: string;
    category: "special" | "status" | "regular";
    type: string;
    priority: number; // For layout grouping
    color?: string; // For status fields
}

// Unified field processing - combines all field types into a single structure
const getAllFieldsComputed = computed((): UnifiedField[] => {
    const fields: UnifiedField[] = [];
    const metadata = props.metadata;

    Object.entries(metadata).forEach(([key, value]) => {
        // Skip lock fields
        if (isLockField(key)) return;

        let field: UnifiedField;

        if (isSpecialField(key)) {
            field = {
                key,
                value,
                displayName: getSpecialFieldTitle(key),
                category: "special",
                type: "special",
                priority: 1, // Highest priority - renders first
            };
        } else if (isStatusField(key)) {
            field = {
                key,
                value,
                displayName: formatFieldName(key),
                category: "status",
                type: "status",
                priority: 1, // Same priority as special fields to appear in same row
                color: getStatusBadgeColor(value),
            };
        } else {
            // Regular field - determine type
            let type: string;
            if (isVectorField(value)) type = "vector";
            else if (typeof value === "number") type = "number";
            else if (typeof value === "boolean") type = "boolean";
            else if (isNumericString(value)) type = "number";
            else if (typeof value === "string" && isLongString(value)) type = "longString";
            else type = "shortString";

            // Set priority based on type for logical grouping
            let priority = 2;
            if (type === "number" || type === "boolean") priority = 2;
            else if (type === "shortString") priority = 3;
            else if (type === "vector") priority = 4;
            else if (type === "longString") priority = 5;

            field = {
                key,
                value,
                displayName: formatFieldName(key),
                category: "regular",
                type,
                priority,
            };
        }

        fields.push(field);
    });

    // Sort by priority, then by display name
    return fields.sort((a, b) => {
        if (a.priority !== b.priority) {
            return a.priority - b.priority;
        }
        return a.displayName.localeCompare(b.displayName);
    });
});

// Group fields for layout purposes - maintains visual separation while using unified structure
const getGroupedFieldsComputed = computed(() => {
    const allFields = getAllFieldsComputed.value;
    const groups: Array<{ priority: number; fields: UnifiedField[] }> = [];

    // Group by priority for visual separation
    const groupMap = new Map<number, UnifiedField[]>();
    allFields.forEach((field) => {
        if (!groupMap.has(field.priority)) {
            groupMap.set(field.priority, []);
        }
        groupMap.get(field.priority)!.push(field);
    });

    // Convert to array format expected by template
    Array.from(groupMap.entries())
        .sort(([a], [b]) => a - b)
        .forEach(([priority, fields]) => {
            groups.push({ priority, fields });
        });

    return groups;
});

// UNIFIED STYLING FUNCTIONS - Replace multiple similar functions with single unified ones

// Color scheme definitions for different field categories
const colorSchemes = {
    special: {
        bg: "bg-indigo-100/60 dark:bg-indigo-950/50",
        hover: "hover:bg-indigo-200/70 dark:hover:bg-indigo-900/60",
        border: "border-indigo-200 dark:border-indigo-700",
        iconBg: "bg-indigo-100 dark:bg-indigo-900",
        iconText: "text-indigo-600 dark:text-indigo-400",
        headerText: "text-indigo-700 dark:text-indigo-300",
    },
    status: {
        success: {
            bg: "bg-green-100/60 dark:bg-green-950/50",
            hover: "hover:bg-green-200/70 dark:hover:bg-green-900/60",
            border: "border-green-200 dark:border-green-700",
            iconBg: "bg-green-100 dark:bg-green-900",
            iconText: "text-green-600 dark:text-green-400",
            headerText: "text-green-700 dark:text-green-300",
        },
        warning: {
            bg: "bg-yellow-100/60 dark:bg-yellow-950/50",
            hover: "hover:bg-yellow-200/70 dark:hover:bg-yellow-900/60",
            border: "border-yellow-200 dark:border-yellow-700",
            iconBg: "bg-yellow-100 dark:bg-yellow-900",
            iconText: "text-yellow-600 dark:text-yellow-400",
            headerText: "text-yellow-700 dark:text-yellow-300",
        },
        error: {
            bg: "bg-red-100/60 dark:bg-red-950/50",
            hover: "hover:bg-red-200/70 dark:hover:bg-red-900/60",
            border: "border-red-200 dark:border-red-700",
            iconBg: "bg-red-100 dark:bg-red-900",
            iconText: "text-red-600 dark:text-red-400",
            headerText: "text-red-700 dark:text-red-300",
        },
        info: {
            bg: "bg-blue-100/60 dark:bg-blue-950/50",
            hover: "hover:bg-blue-200/70 dark:hover:bg-blue-900/60",
            border: "border-blue-200 dark:border-blue-700",
            iconBg: "bg-blue-100 dark:bg-blue-900",
            iconText: "text-blue-600 dark:text-blue-400",
            headerText: "text-blue-700 dark:text-blue-300",
        },
        primary: {
            bg: "bg-purple-100/60 dark:bg-purple-950/50",
            hover: "hover:bg-purple-200/70 dark:hover:bg-purple-900/60",
            border: "border-purple-200 dark:border-purple-700",
            iconBg: "bg-purple-100 dark:bg-purple-900",
            iconText: "text-purple-600 dark:text-purple-400",
            headerText: "text-purple-700 dark:text-purple-300",
        },
        neutral: {
            bg: "bg-gray-100/60 dark:bg-gray-950/50",
            hover: "hover:bg-gray-200/70 dark:hover:bg-gray-900/60",
            border: "border-gray-200 dark:border-gray-700",
            iconBg: "bg-gray-100 dark:bg-gray-900",
            iconText: "text-gray-600 dark:text-gray-400",
            headerText: "text-gray-700 dark:text-gray-300",
        },
    },
    regular: {
        number: {
            bg: "bg-blue-50 dark:bg-blue-950",
            border: "border-blue-200 dark:border-blue-800",
            gradient: "from-blue-400 to-blue-600",
            iconBg: "bg-blue-200 dark:bg-blue-800",
            iconText: "text-blue-700 dark:text-blue-300",
            headerText: "text-blue-800 dark:text-blue-200",
        },
        boolean: {
            bg: "bg-green-50 dark:bg-green-950",
            border: "border-green-200 dark:border-green-800",
            gradient: "from-green-400 to-green-600",
            iconBg: "bg-green-200 dark:bg-green-800",
            iconText: "text-green-700 dark:text-green-300",
            headerText: "text-green-800 dark:text-green-200",
        },
        vector: {
            bg: "bg-purple-50 dark:bg-purple-950",
            border: "border-purple-200 dark:border-purple-800",
            gradient: "from-purple-400 to-purple-600",
            iconBg: "bg-purple-200 dark:bg-purple-800",
            iconText: "text-purple-700 dark:text-purple-300",
            headerText: "text-purple-800 dark:text-purple-200",
        },
        longString: {
            bg: "bg-amber-50 dark:bg-amber-950",
            border: "border-amber-200 dark:border-amber-800",
            gradient: "from-amber-400 to-amber-600",
            iconBg: "bg-amber-200 dark:bg-amber-800",
            iconText: "text-amber-700 dark:text-amber-300",
            headerText: "text-amber-800 dark:text-amber-200",
        },
        shortString: {
            bg: "bg-slate-50 dark:bg-slate-900",
            border: "border-slate-200 dark:border-slate-700",
            gradient: "from-slate-400 to-slate-600",
            iconBg: "bg-slate-200 dark:bg-slate-700",
            iconText: "text-slate-700 dark:text-slate-300",
            headerText: "text-slate-800 dark:text-slate-200",
        },
    },
};

// Unified styling functions
const getUnifiedFieldColorClass = (field: UnifiedField): string => {
    if (field.category === "special") {
        const scheme = colorSchemes.special;
        return `${scheme.bg} ${scheme.hover} ${scheme.border}`;
    } else if (field.category === "status") {
        const scheme =
            colorSchemes.status[field.color as keyof typeof colorSchemes.status] || colorSchemes.status.neutral;
        return `${scheme.bg} ${scheme.hover} ${scheme.border}`;
    } else {
        const scheme =
            colorSchemes.regular[field.type as keyof typeof colorSchemes.regular] || colorSchemes.regular.shortString;
        return `${scheme.bg} ${scheme.border}`;
    }
};

const getUnifiedBorderClass = (field: UnifiedField): string => {
    if (field.category === "special") {
        return colorSchemes.special.border;
    } else if (field.category === "status") {
        const scheme =
            colorSchemes.status[field.color as keyof typeof colorSchemes.status] || colorSchemes.status.neutral;
        return scheme.border;
    } else {
        const scheme =
            colorSchemes.regular[field.type as keyof typeof colorSchemes.regular] || colorSchemes.regular.shortString;
        return scheme.border;
    }
};

const getUnifiedIconContainerClass = (field: UnifiedField): string => {
    const baseClass = "w-4 h-4";

    if (field.category === "special") {
        return `${baseClass} rounded`;
    } else if (field.category === "status") {
        return `${baseClass} rounded`;
    } else {
        return `w-3 h-3 rounded-full text-[9px]`;
    }
};

const getUnifiedIconClass = (field: UnifiedField): string => {
    if (field.category === "special") {
        return colorSchemes.special.iconBg;
    } else if (field.category === "status") {
        const scheme =
            colorSchemes.status[field.color as keyof typeof colorSchemes.status] || colorSchemes.status.neutral;
        return scheme.iconBg;
    } else {
        const scheme =
            colorSchemes.regular[field.type as keyof typeof colorSchemes.regular] || colorSchemes.regular.shortString;
        return scheme.iconBg;
    }
};

const getUnifiedIconTextClass = (field: UnifiedField): string => {
    if (field.category === "special") {
        return colorSchemes.special.iconText;
    } else if (field.category === "status") {
        const scheme =
            colorSchemes.status[field.color as keyof typeof colorSchemes.status] || colorSchemes.status.neutral;
        return scheme.iconText;
    } else {
        const scheme =
            colorSchemes.regular[field.type as keyof typeof colorSchemes.regular] || colorSchemes.regular.shortString;
        return scheme.iconText;
    }
};

const getUnifiedHeaderTextClass = (field: UnifiedField): string => {
    if (field.category === "special") {
        return colorSchemes.special.headerText;
    } else if (field.category === "status") {
        const scheme =
            colorSchemes.status[field.color as keyof typeof colorSchemes.status] || colorSchemes.status.neutral;
        return scheme.headerText;
    } else {
        const scheme =
            colorSchemes.regular[field.type as keyof typeof colorSchemes.regular] || colorSchemes.regular.shortString;
        return scheme.headerText;
    }
};

const getUnifiedGradientClass = (field: UnifiedField): string => {
    if (field.category === "regular") {
        const scheme =
            colorSchemes.regular[field.type as keyof typeof colorSchemes.regular] || colorSchemes.regular.shortString;
        return scheme.gradient;
    }
    return "";
};

const getUnifiedFieldIcon = (field: UnifiedField): string => {
    if (field.category === "special") {
        return getSpecialFieldIcon(field.key);
    } else if (field.category === "status") {
        return getStatusFieldIcon(field.key);
    } else {
        return getTypeIcon(field.type);
    }
};

// Grid span calculation for unified fields
const getUnifiedGridSpanClass = (field: UnifiedField): string => {
    if (field.category === "special") {
        return getSpecialFieldSpanClass(
            field.value,
            getAllFieldsComputed.value.filter((f) => f.category === "status").length,
        );
    } else if (field.category === "status") {
        return getStatusFieldSpanClass(field.value);
    } else {
        return getGridSpanClass(field.key, field.value, field.type);
    }
};

// Value display functions
const getUnifiedDisplayValue = (field: UnifiedField): string => {
    if (field.type === "vector") {
        return formatVectorPreview(field.value as unknown[]);
    } else if (field.type === "number") {
        const displayValue = getDisplayValue(field.value);
        return isSizeField(field.key) ? formatSizeInGiB(displayValue) : formatShortValue(displayValue);
    } else {
        return formatShortValue(field.value);
    }
};

const getUnifiedFieldValueTitle = (field: UnifiedField): string => {
    return getFieldValueTitle(field.key, field.value, field.type);
};

const getUnifiedValueDisplayClass = (field: UnifiedField): string => {
    const classes = [];

    if (field.type === "vector") {
        classes.push("font-mono text-xs");
    } else if (field.type === "number" || field.type === "boolean") {
        classes.push("text-center font-semibold");
    } else if (field.type === "shortString" || field.type === "longString") {
        classes.push("font-medium");
    }

    if (field.type !== "longString") {
        classes.push("truncate");
    }

    return classes.join(" ");
};

const getUnifiedLockButtonSize = (field: UnifiedField): string => {
    return field.category === "regular" ? "w-4 h-4" : "w-3 h-3";
};

const getUnifiedLockTitle = (field: UnifiedField): string => {
    if (!isAuthenticated.value) {
        return `Field is ${
            isFieldLocked(field.key) ? "locked" : "unlocked"
        } - You need to be logged in to modify locks`;
    }
    return isFieldLocked(field.key) ? `Unlock ${field.displayName}` : `Lock ${field.displayName}`;
};

// Helper functions for special fields
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

// Optimized lazy loading for ALL metadata (always render efficiently)
const renderedFieldsByType = computed(() => {
    // Always show all fields - no lazy loading needed
    return processedFields.value.fieldsByType;
});

// Replace individual functions with computed access to memoized results
const getSpecialFieldsComputed = () => processedFields.value.specialFields;
const getStatusFieldsComputed = () => processedFields.value.statusFields;
const getFieldsByTypeComputed = () => renderedFieldsByType.value;

// Determine column span for special fields based on content length and status fields presence
const getSpecialFieldSpanClass = (value: unknown, statusFieldsCount: number): string => {
    const stringValue = String(value);
    const isLong = stringValue.length > 60; // Reduced threshold for more compact layout

    // If there are status fields, we need to reserve space for them
    if (statusFieldsCount > 0) {
        // Reserve less space for status fields (2 columns each, up to 3 status fields = 6 columns max)
        const statusColumnsReserved = Math.min(statusFieldsCount * 2, 6);
        const availableColumns = 12 - statusColumnsReserved;

        if (isLong) {
            // Long content takes all remaining space after status fields
            if (availableColumns >= 6) return "col-span-6";
            if (availableColumns >= 4) return "col-span-4";
            return "col-span-3";
        } else {
            // Short content takes most of remaining space
            if (availableColumns >= 8) return "col-span-5";
            if (availableColumns >= 6) return "col-span-4";
            if (availableColumns >= 4) return "col-span-3";
            return "col-span-3";
        }
    }

    // No status fields, use original logic
    return isLong ? "col-span-12" : "col-span-6";
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

// Status field styling functions
const getStatusFieldSpanClass = (value: unknown): string => {
    // Status fields are typically shorter, so use smaller spans (2 columns max)
    const stringValue = String(value);
    return stringValue.length > 20 ? "col-span-2" : "col-span-2";
};

const getStatusFieldColorClass = (color: string): string => {
    switch (color) {
        case "success":
            return "bg-green-100/60 dark:bg-green-950/50 hover:bg-green-200/70 dark:hover:bg-green-900/60 border-green-200 dark:border-green-700";
        case "warning":
            return "bg-yellow-100/60 dark:bg-yellow-950/50 hover:bg-yellow-200/70 dark:hover:bg-yellow-900/60 border-yellow-200 dark:border-yellow-700";
        case "error":
            return "bg-red-100/60 dark:bg-red-950/50 hover:bg-red-200/70 dark:hover:bg-red-900/60 border-red-200 dark:border-red-700";
        case "info":
            return "bg-blue-100/60 dark:bg-blue-950/50 hover:bg-blue-200/70 dark:hover:bg-blue-900/60 border-blue-200 dark:border-blue-700";
        case "primary":
            return "bg-purple-100/60 dark:bg-purple-950/50 hover:bg-purple-200/70 dark:hover:bg-purple-900/60 border-purple-200 dark:border-purple-700";
        default: // neutral
            return "bg-gray-100/60 dark:bg-gray-950/50 hover:bg-gray-200/70 dark:hover:bg-gray-900/60 border-gray-200 dark:border-gray-700";
    }
};

const getStatusIconBgClass = (color: string): string => {
    switch (color) {
        case "success":
            return "bg-green-100 dark:bg-green-900";
        case "warning":
            return "bg-yellow-100 dark:bg-yellow-900";
        case "error":
            return "bg-red-100 dark:bg-red-900";
        case "info":
            return "bg-blue-100 dark:bg-blue-900";
        case "primary":
            return "bg-purple-100 dark:bg-purple-900";
        default: // neutral
            return "bg-gray-100 dark:bg-gray-900";
    }
};

const getStatusIconTextClass = (color: string): string => {
    switch (color) {
        case "success":
            return "text-green-600 dark:text-green-400";
        case "warning":
            return "text-yellow-600 dark:text-yellow-400";
        case "error":
            return "text-red-600 dark:text-red-400";
        case "info":
            return "text-blue-600 dark:text-blue-400";
        case "primary":
            return "text-purple-600 dark:text-purple-400";
        default: // neutral
            return "text-gray-600 dark:text-gray-400";
    }
};

const getStatusTitleTextClass = (color: string): string => {
    switch (color) {
        case "success":
            return "text-green-700 dark:text-green-300";
        case "warning":
            return "text-yellow-700 dark:text-yellow-300";
        case "error":
            return "text-red-700 dark:text-red-300";
        case "info":
            return "text-blue-700 dark:text-blue-300";
        case "primary":
            return "text-purple-700 dark:text-purple-300";
        default: // neutral
            return "text-gray-700 dark:text-gray-300";
    }
};

const getStatusFieldBorderClass = (color: string): string => {
    switch (color) {
        case "success":
            return "border-green-200 dark:border-green-700";
        case "warning":
            return "border-yellow-200 dark:border-yellow-700";
        case "error":
            return "border-red-200 dark:border-red-700";
        case "info":
            return "border-blue-200 dark:border-blue-700";
        case "primary":
            return "border-purple-200 dark:border-purple-700";
        default: // neutral
            return "border-gray-200 dark:border-gray-700";
    }
};

const getStatusFieldIcon = (key: string): string => {
    const normalizedKey = key.toLowerCase();
    if (normalizedKey.includes("status")) return "📊";
    if (normalizedKey.includes("state")) return "🏃";
    if (normalizedKey.includes("phase")) return "🔄";
    if (normalizedKey.includes("health")) return "💚";
    if (normalizedKey.includes("condition")) return "⚡";
    if (normalizedKey.includes("progress")) return "📈";
    return "🔧"; // Default status icon
};
</script>
