<template>
    <!-- v-memo to prevent unnecessary re-renders when props hasn't changed -->
    <!-- v-memo to prevent unnecessary re-renders when props haven't changed -->
    <div
        class="rounded border-t bg-white"
        style="border-color: var(--theme-light-border-primary)"
        v-memo="[props.entityId, Object.keys(props.metadata).length, editState?.isEditing]"
    >
        <!-- Editing Mode -->
        <div v-if="editState?.isEditing" class="p-6">
            <div class="flex items-center justify-between mb-4">
                <div>
                    <h4 class="text-lg font-semibold">Edit Metadata</h4>
                    <p class="text-sm mt-1">
                        Modify the JSON metadata for this {{ mainTableDisplayName.toLowerCase().slice(0, -1) }}
                    </p>
                </div>
                <div class="flex gap-2">
                    <UButton
                        icon="i-heroicons-check"
                        class="text-white bg-eco-600 hover:bg-eco-700 border-eco-600 hover:border-eco-700"
                        variant="solid"
                        size="sm"
                        :disabled="!isAuthenticated"
                        @click="saveMetadata"
                    >
                        {{ isAuthenticated ? "Save Changes" : "Login Required" }}
                    </UButton>
                    <UButton
                        icon="i-heroicons-x-mark"
                        class="text-neutral-600 bg-neutral-100 hover:bg-neutral-200 border-neutral-300"
                        variant="outline"
                        size="sm"
                        @click="cancelEdit"
                    >
                        Cancel
                    </UButton>
                </div>
            </div>

            <div class="bg-space-50 rounded-lg p-4">
                <UTextarea
                    v-model="localEditJson"
                    :rows="getTextareaRows()"
                    placeholder="Edit metadata JSON..."
                    resize
                    class="font-mono text-sm w-full"
                    autofocus
                />
                <div class="flex items-center justify-between mt-3 text-xs">
                    <span>{{ getJsonStats(localEditJson) }}</span>
                    <div class="flex items-center gap-2">
                        <UButton
                            icon="i-heroicons-arrow-path"
                            class="text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100"
                            variant="ghost"
                            size="xs"
                            @click="formatJson"
                        >
                            Format JSON
                        </UButton>
                        <UButton
                            icon="i-heroicons-clipboard"
                            class="text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100"
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
            <div
                class="flex items-center justify-between px-2 py-1 border-neutral-200"
                style="border-color: var(--theme-light-border-primary)"
            >
                <div>
                    <h4 class="text-xs font-medium">Metadata ({{ visibleFieldCount }} fields)</h4>
                </div>
                <UButton
                    icon="i-heroicons-pencil"
                    class="text-neutral-600 hover:text-neutral-800 hover:bg-neutral-100"
                    variant="ghost"
                    size="xs"
                    @click="enterEditMode"
                >
                    Edit
                </UButton>
            </div>
            <!-- Compact Content -->
            <div class="px-2">
                <!-- Unified Fields Grid Layout -->
                <div v-if="getAllFieldsComputed.length > 0" class="space-y-2">
                    <!-- Group fields by display row priority -->
                    <template v-for="fieldGroup in getGroupedFieldsComputed" :key="fieldGroup.priority">
                        <div class="grid grid-cols-12 gap-2 text-xs">
                            <template v-for="field in fieldGroup.fields" :key="field.key">
                                <!-- Unified Field Card -->
                                <div
                                    :class="[getUnifiedGridSpanClass(field), getUnifiedFieldColorClass(field)]"
                                    :style="getUnifiedFieldStyle(field)"
                                    class="group relative overflow-hidden rounded border transition-colors duration-200 shadow-sm"
                                >
                                    <!-- Background gradient (only for regular fields) -->
                                    <div
                                        v-if="field.category === 'regular'"
                                        class="absolute inset-0 opacity-5 group-hover:opacity-10 transition-opacity duration-200"
                                        :style="getUnifiedGradientStyle(field)"
                                    />

                                    <!-- Unified Field Header -->
                                    <div
                                        class="relative flex items-center justify-between px-2 py-1 border-b border-opacity-20"
                                        :style="[getUnifiedBorderStyle(field), getUnifiedFieldStyle(field, true)]"
                                    >
                                        <div class="flex items-center gap-1.5 flex-1 min-w-0">
                                            <!-- Unified icon -->
                                            <div
                                                :class="getUnifiedIconContainerClass(field)"
                                                :style="getUnifiedIconStyle(field)"
                                            >
                                                <span class="text-[11px]">
                                                    {{ getUnifiedFieldIcon(field) }}
                                                </span>
                                            </div>
                                            <!-- Field title -->
                                            <span
                                                class="font-medium text-xs truncate"
                                                :style="getUnifiedHeaderTextStyle(field)"
                                                :title="field.displayName"
                                            >
                                                {{ field.displayName }}
                                            </span>
                                        </div>

                                        <!-- Special badges/indicators - using :color for dynamic behavior -->
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
                                            <!-- Lock indicator - using :color prop for component behavior -->
                                            <UButton
                                                :icon="
                                                    isFieldLocked(field.key)
                                                        ? 'i-heroicons-lock-closed'
                                                        : 'i-heroicons-lock-open'
                                                "
                                                :color="isFieldLocked(field.key) ? 'eco' : 'neutral'"
                                                variant="ghost"
                                                size="xs"
                                                :padded="false"
                                                :disabled="!isAuthenticated"
                                                :class="[
                                                    getUnifiedLockButtonSize(field),
                                                    {
                                                        'cursor-pointer opacity-70 hover:opacity-100': isAuthenticated,
                                                        'cursor-not-allowed opacity-50': !isAuthenticated,
                                                    },
                                                ]"
                                                class="transition-all duration-200"
                                                :title="getUnifiedLockTitle(field)"
                                                @click="isAuthenticated ? toggleFieldLock(field.key) : undefined"
                                            />

                                            <!-- Copy button - using Tailwind classes -->
                                            <UButton
                                                icon="i-heroicons-clipboard-document"
                                                :class="[
                                                    getUnifiedLockButtonSize(field),
                                                    'text-neutral-500 hover:text-info-600 hover:bg-neutral-100 cursor-pointer opacity-70 hover:opacity-100 transition-all duration-200',
                                                ]"
                                                variant="ghost"
                                                size="xs"
                                                :padded="false"
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
import { getSemanticColor, getThemeColor, type SemanticColorKey } from "~/config/colors";
import { reduceEachLeadingCommentRange } from "typescript";

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

// Dynamic color system based on FCC design philosophy using CSS custom properties
const { $colorMode } = useNuxtApp();
const isDark = computed(() => $colorMode?.value === "dark");

// FCC-aligned color system for metadata fields using CSS variables
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

// UNIFIED STYLING FUNCTIONS - Preference for Tailwind classes over CSS variables

// Helper function to generate Tailwind class names for custom colors
const getFieldColorClasses = (field: UnifiedField) => {
    const semanticColor = getSemanticColorForFieldType(resolveFieldSemanticColor(field));
    return {
        // Background classes
        bg50: `bg-${semanticColor}-50`,
        bg100: `bg-${semanticColor}-100`,
        bg300: `bg-${semanticColor}-300`,
        // Border classes
        border200: `border-${semanticColor}-200`,
        // Text classes
        text600: `text-${semanticColor}-600`,
        text700: `text-${semanticColor}-700`,
        text800: `text-${semanticColor}-800`,
        // Hover classes
        hoverBg100: `hover:bg-${semanticColor}-100`,
        hoverText700: `hover:text-${semanticColor}-700`,
    };
};

const getUnifiedIconContainerClass = (field: UnifiedField): string => {
    const baseClass = "flex-shrink-0 flex items-center justify-center";
    const colorClasses = getFieldColorClasses(field);

    if (field.category === "special") {
        return `${baseClass} w-4 h-4 rounded ${colorClasses.bg300} ${colorClasses.text800}`;
    } else if (field.category === "status") {
        return `${baseClass} w-4 h-4 rounded ${colorClasses.bg300} ${colorClasses.text800}`;
    } else {
        return `${baseClass} w-4 h-4 rounded-full text-[9px] bg-deep-blue-900 text-white`;
    }
};

const getUnifiedGradientStyle = (field: UnifiedField): Record<string, string> => {
    if (field.category === "regular") {
        const colors = getFieldColorsMemoized(field);
        return {
            background: `linear-gradient(to bottom right, ${colors.grad400}, ${colors.grad600})`,
        };
    }
    return {};
};

// Enhanced color scheme mapping based on field categories and FCC design principles using CSS variables
const getSemanticColorForFieldType = (fieldType: string): string => {
    const typeMapping: Record<string, string> = {
        // Scientific data types - align with FCC's scientific excellence value
        number: "gray", // Radiant blue for quantitative data
        boolean: "success", // Eco green for binary/environmental states
        vector: "accent", // Energy purple for complex particle data

        // Content types - align with FCC's open communication values
        longString: "accent", // Earth tones for descriptive content
        shortString: "gray", // Gray for basic textual information

        // Metadata categories - align with FCC's transparency value
        special: "secondary",
        status: "secondary", // Radiant blue for status/state information

        // Status-specific colors - align with universal status conventions
        success: "eco",
        warning: "warning",
        error: "error",
        info: "info",
        neutral: "earth",
    };

    return typeMapping[fieldType] || "earth";
};

// Generate CSS variable references for color schemes
const getCSSVariableForColor = (semantic: string, shade: string | number = "500") => {
    return `var(--color-${semantic}-${shade})`;
};

// CENTRALIZED COLOR RESOLUTION - Eliminates code duplication
const resolveFieldSemanticColor = (field: UnifiedField): string => {
    if (field.category === "status" && field.color) {
        return field.color;
    } else if (field.category === "special") {
        return "special";
    } else {
        return field.type;
    }
};

// Centralized color variables generator - further simplification
const getFieldColorVariables = (field: UnifiedField) => {
    const semanticColor = getSemanticColorForFieldType(resolveFieldSemanticColor(field));
    return {
        bg50: getCSSVariableForColor(semanticColor, "50"),
        bg100: getCSSVariableForColor(semanticColor, "100"),
        bg300: getCSSVariableForColor(semanticColor, "300"),
        border200: getCSSVariableForColor(semanticColor, "200"),
        text600: getCSSVariableForColor(semanticColor, "600"),
        text700: getCSSVariableForColor(semanticColor, "700"),
        grad400: getCSSVariableForColor(semanticColor, "400"),
        grad600: getCSSVariableForColor(semanticColor, "600"),
        main: getCSSVariableForColor(semanticColor, "main"),
    };
};

// Memoization for color computation - ultimate optimization
const colorMemo = new Map<string, ReturnType<typeof getFieldColorVariables>>();
const getFieldColorsMemoized = (field: UnifiedField) => {
    const key = `${field.category}-${field.type}-${field.color || ""}`;
    if (!colorMemo.has(key)) {
        colorMemo.set(key, getFieldColorVariables(field));
    }
    return colorMemo.get(key)!;
};

// UNIFIED STYLING FUNCTIONS - CSS Variable-based dynamic color system

const getUnifiedFieldColorClass = (field: UnifiedField): string => {
    return "group relative overflow-hidden rounded border transition-colors duration-200 shadow-sm";
};

const getUnifiedFieldStyle = (field: UnifiedField, isHeader: Boolean = false): Record<string, string> => {
    const colors = getFieldColorsMemoized(field);
    return {
        backgroundColor: isHeader ? colors.bg300 : colors.bg50,
        borderColor: colors.border200,
        "--hover-bg-color": colors.bg100,
    };
};

const getUnifiedBorderStyle = (field: UnifiedField): Record<string, string> => {
    const colors = getFieldColorsMemoized(field);
    return {
        borderColor: colors.border200,
    };
};

const getUnifiedIconStyle = (field: UnifiedField): Record<string, string> => {
    const colors = getFieldColorsMemoized(field);
    return {
        backgroundColor: "var(--color-deep-blue-main)",
        color: colors.text600,
    };
};

const getUnifiedHeaderTextStyle = (field: UnifiedField): Record<string, string> => {
    // Using Tailwind classes is preferred, but this function returns inline styles for dynamic cases
    return {
        // For dynamic colors based on field types, we still need CSS variables
        // But for static cases, prefer Tailwind classes in the template
    };
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
        classes.push("text-center");
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

// Status field styling functions - updated to use CSS variables
const getStatusFieldSpanClass = (value: unknown): string => {
    const stringValue = String(value);
    return stringValue.length > 20 ? "col-span-2" : "col-span-2";
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

<style scoped>
/* FCC-aligned dynamic color system using CSS custom properties */
/* This style block generates theme-aware colors based on the FCC design philosophy */

/* Component uses inline styles for dynamic colors via Vue's :style binding */
/* CSS custom properties are generated from the colors.ts configuration */

/* Enhanced hover effects for interactive elements */
.group:hover {
    background-color: var(--hover-bg-color, inherit) !important;
}

/* Ensure hover transitions are smooth */
.group {
    transition: background-color 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* Smooth transitions for color changes */
.transition-colors {
    transition-property: background-color, border-color, color;
    transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
    transition-duration: 200ms;
}

/* Enhanced hover effects for buttons */
[style*="--hover-color"]:hover {
    color: var(--hover-color) !important;
}

/* Typography hierarchy following FCC design principles */
.font-medium {
    font-weight: 500;
}

.text-xs {
    font-size: 0.75rem;
    line-height: 1rem;
}

.text-sm {
    font-size: 0.875rem;
    line-height: 1.25rem;
}

.text-lg {
    font-size: 1.125rem;
    line-height: 1.75rem;
}

/* Grid system for responsive field layout */
.grid-cols-12 {
    grid-template-columns: repeat(12, minmax(0, 1fr));
}

/* Enhanced shadow system for depth and hierarchy */
.shadow-sm {
    box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}

/* Border radius following FCC design system */
.rounded {
    border-radius: 0.25rem;
}

.rounded-lg {
    border-radius: 0.5rem;
}

.rounded-full {
    border-radius: 9999px;
}

/* Spacing utilities */
.space-y-2 > :not([hidden]) ~ :not([hidden]) {
    margin-top: 0.5rem;
}

.gap-2 {
    gap: 0.5rem;
}

.gap-1 {
    gap: 0.25rem;
}

.gap-1\.5 {
    gap: 0.375rem;
}

/* Opacity utilities for interactive states */
.opacity-5 {
    opacity: 0.05;
}

.opacity-10 {
    opacity: 0.1;
}

.opacity-50 {
    opacity: 0.5;
}

.opacity-70 {
    opacity: 0.7;
}

.hover\:opacity-100:hover {
    opacity: 1;
}

/* Scientific excellence visual enhancements */
.font-mono {
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

/* Accessibility and usability enhancements */
.cursor-pointer {
    cursor: pointer;
}

.cursor-not-allowed {
    cursor: not-allowed;
}

/* Text truncation for overflow content */
.truncate {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
</style>
