<template>
    <UModal
        v-model:open="isOpen"
        title="Dataset Tools"
        :transition="true"
        :close="{
            color: 'neutral',
            variant: 'ghost',
            size: 'xs',
            class: 'w-6 h-6 p-1 hover:bg-gray-100 rounded cursor-pointer shrink-0 flex items-center justify-center',
        }"
    >
        <UButton
            class="cursor-pointer"
            icon="i-heroicons-circle-stack"
            color="neutral"
            variant="ghost"
            :label="iconOnly ? undefined : 'Add Data'"
            @click="isOpen = true"
        />

        <template #body>
            <div class="space-y-6 overflow-hidden">
                <UTabs v-model="activeTab" :items="tabItems" class="w-full">
                    <template #add>
                        <div class="space-y-3 pt-3">
                            <div v-if="!isNavigationReady" class="text-sm text-deep-blue-600">
                                Loading navigation fields...
                            </div>
                            <div v-else class="space-y-3">
                                <div>
                                    <label class="block text-sm font-medium text-deep-blue-900 mb-1">
                                        Dataset Name *
                                    </label>
                                    <UInput v-model="singleName" placeholder="e.g. my-simulation" class="w-full" />
                                </div>

                                <div>
                                    <label class="block text-sm font-medium text-deep-blue-900 mb-1">
                                        DRS Request *
                                    </label>
                                    <UInput v-model="singleDrsRequest" placeholder="e.g. DRS-76" class="w-full" />
                                </div>

                                <div v-for="field in navigationFields" :key="field.type">
                                    <label class="block text-sm font-medium text-deep-blue-900 mb-1">
                                        {{ field.label }} *
                                    </label>
                                    <UInputMenu
                                        v-model="singleNavValues[field.type]"
                                        :items="navigationOptions[field.type] || []"
                                        :loading="navigationOptionsLoading[field.type]"
                                        :create-item="isAdmin"
                                        :placeholder="
                                            isAdmin
                                                ? `Select or type a new ${field.label.toLowerCase()}`
                                                : `Select an existing ${field.label.toLowerCase()}`
                                        "
                                        class="w-full"
                                        @create="(term: string) => handleNavigationOptionCreate(field.type, term)"
                                    />
                                    <p v-if="!isAdmin" class="text-xs text-deep-blue-500 mt-1">
                                        Only admins can register a new {{ field.label.toLowerCase() }}.
                                    </p>
                                </div>

                                <div>
                                    <label class="block text-sm font-medium text-deep-blue-900 mb-1">
                                        Metadata (optional JSON object)
                                    </label>
                                    <UTextarea
                                        v-model="singleMetadataText"
                                        placeholder='{"status": "done", "comment": "..."}'
                                        :rows="4"
                                        class="w-full font-mono"
                                    />
                                </div>

                                <UButton
                                    icon="i-heroicons-plus-circle"
                                    color="primary"
                                    variant="solid"
                                    size="sm"
                                    :disabled="singleProcessing"
                                    :loading="singleProcessing"
                                    class="cursor-pointer"
                                    @click="performSingleCreate"
                                >
                                    {{ singleProcessing ? "Creating..." : "Create Dataset" }}
                                </UButton>

                                <div v-if="singleStatusMessage" class="text-xs" :class="singleStatusMessageClass">
                                    {{ singleStatusMessage }}
                                </div>
                            </div>
                        </div>
                    </template>

                    <template #bulk>
                <!-- Add/Update Datasets Section -->
                <div class="space-y-3 pt-3">
                    <h3 class="text-md font-medium text-deep-blue-900 flex items-center gap-2">
                        <UIcon name="i-heroicons-cog-6-tooth" class="text-lg text-secondary-500" />
                        Add or update datasets from a JSON file
                        <UTooltip
                            text="Learn more about adding/updating datasets"
                            class="cursor-pointer"
                            :popper="{ placement: 'bottom' }"
                        >
                            <UButton
                                variant="ghost"
                                color="primary"
                                size="xl"
                                class="w-8 h-8 hover:bg-gray-100 rounded-full flex items-center justify-center cursor-pointer"
                                @click="showOverrideHelp = !showOverrideHelp"
                            >
                                <UIcon
                                    name="i-heroicons-information-circle"
                                    style="
                                        width: 24px !important;
                                        height: 24px !important;
                                        min-width: 24px !important;
                                        min-height: 24px !important;
                                    "
                                />
                            </UButton>
                        </UTooltip>
                    </h3>

                    <!-- Expandable Help Section with Transition -->
                    <div
                        class="transition-all duration-300 ease-in-out overflow-hidden"
                        :style="{
                            maxHeight: showOverrideHelp ? '50rem' : '0',
                            opacity: showOverrideHelp ? '1' : '0',
                        }"
                    >
                        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
                            <div class="flex items-center justify-between mb-3">
                                <h4 class="font-semibold text-deep-blue-900 flex items-center gap-2">
                                    <UIcon name="i-heroicons-academic-cap" class="text-deep-blue-600" />
                                    How This Works
                                </h4>
                                <UButton
                                    icon="i-heroicons-x-mark"
                                    color="neutral"
                                    variant="ghost"
                                    size="xs"
                                    class="w-6 h-6 p-1 hover:bg-gray-100 rounded cursor-pointer flex items-center justify-center shrink-0"
                                    @click="showOverrideHelp = false"
                                />
                            </div>

                            <div class="text-sm text-deep-blue-800 space-y-2">
                                <p>
                                    <strong>🆕 No 'uuid'? It's created.</strong> Navigation fields (accelerator,
                                    campaign, detector, etc.) are matched against existing values, and the dataset's
                                    UUID is derived deterministically from its name and those fields. Registering a
                                    brand-new navigation value (not already in the system) requires admin.
                                </p>
                                <p>
                                    <strong>🔁 Has 'uuid'? It's updated.</strong> Only metadata fields are touched on
                                    the matching existing entity -- database fields like foreign keys and names are
                                    protected and blocked. Fails that entry if no entity with that UUID exists.
                                </p>
                                <p>
                                    <strong>🔒 Field Locking:</strong> Updated metadata fields are automatically locked
                                    to prevent further changes (unless force override is used).
                                </p>
                                <p>
                                    <strong>🔄 Independent Processing:</strong> New entries and updates are processed
                                    independently -- one entry failing doesn't block the others from succeeding.
                                </p>
                            </div>

                            <div class="space-y-2">
                                <h5 class="font-medium text-deep-blue-900">Example JSON Format:</h5>
                                <pre
                                    class="bg-gray-100 p-3 rounded text-sm font-mono overflow-x-auto text-deep-blue-800"
                                >
{
  "datasets": [
    {
      "dataset-name": "new-simulation",
      "drs-request": "DRS-76",
      "accelerator": "fcc-ee",
      "campaign": "winter2023",
      "status": "completed"
    },
    {
      "uuid": "existing-entity-uuid-here",
      "comment": "Updated via upload",
      "status": "done"
    }
  ]
}</pre
                                >
                            </div>
                        </div>
                    </div>

                    <div class="space-y-2">
                        <!-- File Selection -->
                        <div class="flex items-center gap-2">
                            <UButton
                                icon="i-heroicons-folder-open"
                                color="neutral"
                                variant="outline"
                                size="sm"
                                class="cursor-pointer"
                                @click="triggerFileInput"
                            >
                                Select JSON File
                            </UButton>
                        </div>

                        <!-- Hidden file input -->
                        <input
                            ref="fileInput"
                            type="file"
                            accept=".json"
                            class="hidden"
                            @change="handleFileSelection"
                        >

                        <!-- Force Override Checkbox -->
                        <div class="flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                            <UCheckbox id="force-override" v-model="forceOverride" color="warning" />
                            <label for="force-override" class="flex items-center gap-2 text-sm cursor-pointer">
                                <UIcon name="i-heroicons-exclamation-triangle" class="text-lg text-amber-600" />
                                <span class="font-medium text-md text-amber-800">Force Override Locked Fields</span>
                                <span
                                    class="inline-flex items-center cursor-pointer"
                                    title="When enabled, this will override entity values even if the fields are currently locked by other users. Use with caution - this can overwrite changes made by other users and may cause data conflicts."
                                >
                                    <UIcon
                                        name="i-heroicons-information-circle"
                                        class="text-amber-600 hover:text-amber-800 cursor-help"
                                        style="
                                            width: 24px !important;
                                            height: 24px !important;
                                            min-width: 24px !important;
                                            min-height: 24px !important;
                                        "
                                    />
                                </span>
                            </label>
                        </div>

                        <!-- Override Button -->
                        <UButton
                            icon="i-heroicons-arrow-up-tray"
                            color="primary"
                            variant="solid"
                            size="sm"
                            :disabled="!selectedFile || isProcessing"
                            :loading="isProcessing"
                            class="cursor-pointer"
                            @click="performUpload"
                        >
                            {{ isProcessing ? "Processing..." : "Upload Datasets" }}
                        </UButton>

                        <!-- Status Messages -->
                        <div v-if="statusMessage" class="text-xs text-secondary" :class="statusMessageClass">
                            {{ statusMessage }}
                        </div>

                        <!-- Lock Conflicts Details -->
                        <div v-if="lockConflicts && lockConflicts.length > 0" class="mt-4 space-y-3">
                            <div class="flex items-center justify-between">
                                <h4 class="text-sm font-medium text-red-800 flex items-center gap-2">
                                    <UIcon name="i-heroicons-lock-closed" class="text-red-600" />
                                    Lock Conflicts Details:
                                </h4>
                                <UButton
                                    icon="i-heroicons-clipboard-document"
                                    color="neutral"
                                    variant="outline"
                                    size="xs"
                                    class="cursor-pointer"
                                    @click="copyLockConflictsToClipboard"
                                >
                                    Copy JSON
                                </UButton>
                            </div>
                            <div class="max-h-64 overflow-y-auto space-y-3">
                                <div
                                    v-for="(conflict, index) in lockConflicts"
                                    :key="conflict.entity_uuid"
                                    class="border border-red-300 rounded-lg p-4 bg-red-50 shadow-sm"
                                >
                                    <div class="text-sm font-semibold text-red-900 mb-3 pb-2 border-b border-red-200">
                                        <div class="flex items-center gap-2">
                                            <span class="bg-red-100 text-red-800 px-2 py-1 rounded text-xs font-medium">
                                                Entity #{{ index + 1 }}
                                            </span>
                                            <span class="text-red-800">{{
                                                conflict.entity_data?.name || "Unknown"
                                            }}</span>
                                        </div>
                                        <div class="text-xs text-red-600 font-mono mt-1">
                                            UUID: {{ conflict.entity_uuid }}
                                        </div>
                                    </div>
                                    <div class="space-y-3">
                                        <div
                                            v-for="(fieldInfo, fieldName) in conflict.locked_fields"
                                            :key="fieldName"
                                            class="bg-white rounded border border-red-200 p-3"
                                        >
                                            <div class="flex items-center gap-2 mb-2">
                                                <UIcon name="i-heroicons-lock-closed" class="text-energy-500 text-xs" />
                                                <span class="font-bold text-energy-800 text-sm">{{ fieldName }}</span>
                                                <span
                                                    class="text-xs bg-energy-100 text-energy-700 px-2 py-1 rounded font-medium"
                                                    >LOCKED</span
                                                >
                                            </div>
                                            <div class="text-xs space-y-1 ml-5">
                                                <div class="flex items-start gap-2">
                                                    <span class="font-medium text-dark-blue-900 min-w-[80px]"
                                                        >Current:</span
                                                    >
                                                    <span
                                                        class="font-mono bg-gray-100 px-2 py-1 rounded text-dark-blue-900 break-all"
                                                    >
                                                        {{ fieldInfo.current_value ?? "null" }}
                                                    </span>
                                                </div>
                                                <div class="flex items-start gap-2">
                                                    <span class="font-medium text-energy min-w-[80px]">Attempted:</span>
                                                    <span
                                                        class="font-mono bg-energy-50 px-2 py-1 rounded text-energy break-all"
                                                    >
                                                        {{ fieldInfo.attempted_value ?? "null" }}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                    </template>
                </UTabs>
            </div>
        </template>
    </UModal>
</template>

<script setup lang="ts">
interface Props {
    iconOnly?: boolean;
}

withDefaults(defineProps<Props>(), {
    iconOnly: false,
});

const isOpen = ref(false);

// Refresh the search results once the modal closes, if something actually changed
const needsRefresh = ref(false);
const { forceRefresh } = useGlobalSearchControl();
watch(isOpen, (open) => {
    if (!open && needsRefresh.value) {
        needsRefresh.value = false;
        forceRefresh();
    }
});

// Tabs: single-dataset form vs. bulk JSON upload
const activeTab = ref("add");
const tabItems = [
    { label: "Add Dataset", icon: "i-heroicons-plus-circle", slot: "add" as const, value: "add" },
    { label: "Bulk Upload (JSON)", icon: "i-heroicons-document-text", slot: "bulk" as const, value: "bulk" },
];

// Navigation fields (dynamic, schema-driven)
const { getNavigationOrder, getNavigationItem, initializeNavigation, isNavigationReady: checkNavigationReady } =
    useNavigationConfig();
const isNavigationReady = computed(() => checkNavigationReady());
const navigationFields = computed(() =>
    getNavigationOrder().map((type) => ({ type, label: getNavigationItem(type).label })),
);

// Only admins may register a new navigation value; editors pick from the
// existing list only (also enforced server-side).
const { hasRole } = useAuth();
const isAdmin = computed(() => hasRole("admin"));

onMounted(() => {
    initializeNavigation();
});

// API client (also used by the bulk upload tab below)
const { uploadDatasets, getDropdownOptions } = useApiClient();

const DRS_REQUEST_PATTERN = /^DRS-\d+$/;

// Single-dataset creation form
const singleName = ref("");
const singleDrsRequest = ref("");
const singleMetadataText = ref("");
const singleNavValues = reactive<Record<string, string>>({});
const navigationOptions = reactive<Record<string, string[]>>({});
const navigationOptionsLoading = reactive<Record<string, boolean>>({});
const navigationOptionsLoaded = reactive<Record<string, boolean>>({});
const singleProcessing = ref(false);
const singleStatusMessage = ref("");
const singleStatusMessageClass = ref("");

const loadNavigationOptions = async (type: string) => {
    if (navigationOptionsLoaded[type] || navigationOptionsLoading[type]) return;
    navigationOptionsLoading[type] = true;
    try {
        const items = await getDropdownOptions(type);
        navigationOptions[type] = items.map((item) => item.name);
        navigationOptionsLoaded[type] = true;
    } catch (error) {
        console.error(`Failed to load existing ${type} values:`, error);
        navigationOptions[type] = [];
    } finally {
        navigationOptionsLoading[type] = false;
    }
};

// Drop our own cached dropdown values so the next load picks up anything
// just created (here or elsewhere), instead of serving this tab's stale cache.
const refreshNavigationOptions = () => {
    navigationFields.value.forEach((field) => {
        navigationOptionsLoaded[field.type] = false;
        loadNavigationOptions(field.type);
    });
};

watch(
    navigationFields,
    (fields) => {
        fields.forEach((field) => {
            if (!(field.type in singleNavValues)) {
                singleNavValues[field.type] = "";
            }
            loadNavigationOptions(field.type);
        });
    },
    { immediate: true },
);

const handleNavigationOptionCreate = (type: string, term: string) => {
    singleNavValues[type] = term;
    if (!navigationOptions[type]) {
        navigationOptions[type] = [];
    }
    if (!navigationOptions[type].includes(term)) {
        navigationOptions[type].push(term);
    }
};

const showSingleStatus = (message: string, type: "success" | "error" | "info") => {
    singleStatusMessage.value = message;
    singleStatusMessageClass.value =
        type === "success" ? "text-green-600" : type === "error" ? "text-energy-600" : "text-blue-600";
};

const performSingleCreate = async () => {
    const trimmedName = singleName.value.trim();
    if (!trimmedName) {
        showSingleStatus("Dataset name is required.", "error");
        return;
    }

    const trimmedDrsRequest = singleDrsRequest.value.trim();
    if (!trimmedDrsRequest) {
        showSingleStatus("DRS request reference is required.", "error");
        return;
    }
    if (!DRS_REQUEST_PATTERN.test(trimmedDrsRequest)) {
        showSingleStatus("DRS request must be in the form DRS-<number>, e.g. DRS-76.", "error");
        return;
    }

    const missingFields = navigationFields.value.filter((field) => !singleNavValues[field.type]?.trim());
    if (missingFields.length > 0) {
        showSingleStatus(`Please fill in: ${missingFields.map((field) => field.label).join(", ")}.`, "error");
        return;
    }

    let extraMetadata: Record<string, unknown> = {};
    const metadataText = singleMetadataText.value.trim();
    if (metadataText) {
        try {
            const parsedMetadata = JSON.parse(metadataText);
            if (!parsedMetadata || typeof parsedMetadata !== "object" || Array.isArray(parsedMetadata)) {
                throw new Error("Metadata must be a JSON object, e.g. {\"status\": \"done\"}.");
            }
            extraMetadata = parsedMetadata;
        } catch (error) {
            showSingleStatus(error instanceof Error ? error.message : "Invalid metadata JSON.", "error");
            return;
        }

        const reservedKeys = new Set([
            "dataset-name",
            "name",
            "uuid",
            "drs-request",
            ...navigationFields.value.map((field) => field.type),
        ]);
        const collidingKeys = Object.keys(extraMetadata).filter((key) => reservedKeys.has(key));
        if (collidingKeys.length > 0) {
            showSingleStatus(`Metadata cannot redefine reserved field(s): ${collidingKeys.join(", ")}.`, "error");
            return;
        }
    }

    const dataset: Record<string, unknown> = {
        "dataset-name": trimmedName,
        "drs-request": trimmedDrsRequest,
        ...Object.fromEntries(
            navigationFields.value.map((field) => [field.type, singleNavValues[field.type].trim()]),
        ),
        ...extraMetadata,
    };

    singleProcessing.value = true;
    showSingleStatus("Creating dataset...", "info");

    try {
        const response = (await uploadDatasets([dataset], false)) as UploadResponse;

        if (response.success && response.created_count > 0) {
            showSingleStatus("Dataset created successfully.", "success");
            needsRefresh.value = true;
            invalidateNavigationDropdowns();
            refreshNavigationOptions();
            singleName.value = "";
            singleDrsRequest.value = "";
            singleMetadataText.value = "";
            navigationFields.value.forEach((field) => {
                singleNavValues[field.type] = "";
            });
        } else {
            showSingleStatus(response.message || "Failed to create dataset.", "error");
        }
    } catch (error: unknown) {
        console.error("Dataset creation failed:", error);
        const errorMessage =
            (error as { data?: { detail?: string }; message?: string })?.data?.detail ||
            (error as { message?: string })?.message ||
            "Failed to create dataset.";
        showSingleStatus(errorMessage, "error");
    } finally {
        singleProcessing.value = false;
    }
};

// Upload response type
interface UploadResponse {
    success: boolean;
    message: string;
    created_count: number;
    updated_count: number;
    failed_count: number;
    lock_conflicts?: Array<{
        entity_id: number;
        entity_uuid: string;
        locked_fields: Record<
            string,
            {
                locked: boolean;
                current_value: unknown;
                attempted_value: unknown;
            }
        >;
        entity_data: Record<string, unknown>;
    }>;
    missing_entities?: Array<{
        entity_data: Record<string, unknown>;
        identifier: string;
    }>;
}

// File upload and override functionality
const fileInput = ref<HTMLInputElement>();
const selectedFile = ref<File | null>(null);
const selectedFileName = ref<string>("");
const isProcessing = ref(false);
const statusMessage = ref<string>("");
const statusMessageClass = ref<string>("");
const lockConflicts = ref<UploadResponse["lock_conflicts"]>([]);
const forceOverride = ref<boolean>(false);
const showOverrideHelp = ref<boolean>(false);

// Trigger file input click
const triggerFileInput = () => {
    fileInput.value?.click();
};

// Handle file selection
const handleFileSelection = (event: Event) => {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];

    if (file) {
        selectedFile.value = file;
        selectedFileName.value = file.name;
        statusMessage.value = "";

        // Validate file type
        if (!file.name.toLowerCase().endsWith(".json")) {
            showStatus("Please select a valid JSON file.", "error");
            return;
        }

        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            showStatus("File size must be less than 10MB.", "error");
            return;
        }

        showStatus(`Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, "success");
    }
};

// Show status message with styling
const showStatus = (message: string, type: "success" | "error" | "info") => {
    statusMessage.value = message;
    statusMessageClass.value =
        type === "success" ? "text-green-600" : type === "error" ? "text-energy-600" : "text-blue-600";
};

// Perform the upload operation
const performUpload = async () => {
    if (!selectedFile.value) {
        showStatus("No file selected.", "error");
        return;
    }

    isProcessing.value = true;
    showStatus("Reading and validating file...", "info");

    try {
        // Read file as text
        const fileText = await selectedFile.value.text();

        // Parse JSON
        let parsed;
        try {
            parsed = JSON.parse(fileText);
        } catch {
            throw new Error("Invalid JSON format in selected file.");
        }

        // Validate shape: {"datasets": [...]}
        if (!parsed || !Array.isArray(parsed.datasets)) {
            throw new Error('JSON file must be an object with a "datasets" array.');
        }

        if (parsed.datasets.length === 0) {
            throw new Error("JSON file contains no datasets.");
        }

        // Only confirm when something potentially destructive is happening:
        // updating existing entries by UUID, or bypassing field locks.
        const hasUpdates = parsed.datasets.some(
            (entry: Record<string, unknown>) => !!entry.uuid,
        );
        if (hasUpdates || forceOverride.value) {
            if (!confirm("Are you sure you want to proceed with this upload?")) {
                showStatus("Upload cancelled.", "info");
                isProcessing.value = false;
                return;
            }
        }

        showStatus(`Processing ${parsed.datasets.length} datasets...`, "info");

        const response = (await uploadDatasets(parsed.datasets, forceOverride.value)) as UploadResponse;
        const countsMsg = `${response.created_count} created, ${response.updated_count} updated`;

        if (response.created_count > 0 || response.updated_count > 0) {
            needsRefresh.value = true;
        }
        if (response.created_count > 0) {
            invalidateNavigationDropdowns();
            refreshNavigationOptions();
        }

        if (response.success) {
            showStatus(`Successfully processed: ${countsMsg}.`, "success");
            lockConflicts.value = []; // Clear any previous conflicts

            // Clear the file selection after successful operation
            setTimeout(() => {
                selectedFile.value = null;
                selectedFileName.value = "";
                forceOverride.value = false; // Reset force override
                if (fileInput.value) {
                    fileInput.value.value = "";
                }
            }, 3000);
        } else if (response.missing_entities && response.missing_entities.length > 0) {
            // Handle missing entities/UUIDs error
            const missingCount = response.missing_entities.length;
            const missingList = response.missing_entities
                .slice(0, 3)
                .map((missing) => missing.identifier)
                .join(", ");
            const moreText = missingCount > 3 ? ` and ${missingCount - 3} more` : "";

            showStatus(
                `${countsMsg}; ${missingCount} update(s) failed -- no entity found for UUID(s): ${missingList}${moreText}.`,
                "error",
            );
            lockConflicts.value = [];
        } else if (response.lock_conflicts && response.lock_conflicts.length > 0) {
            lockConflicts.value = response.lock_conflicts;

            // Count total locked fields across all entities
            const totalLockedFields = response.lock_conflicts.reduce(
                (sum, conflict) => sum + Object.keys(conflict.locked_fields).length,
                0,
            );

            showStatus(
                `${countsMsg}; ${response.lock_conflicts.length} entities have ${totalLockedFields} locked fields. See details below.`,
                "error",
            );

            // Log detailed conflict information for debugging
            console.warn("Lock conflicts detected:", response.lock_conflicts);
        } else {
            lockConflicts.value = [];
            showStatus(response.message || "Upload operation failed.", "error");
        }
    } catch (error: unknown) {
        console.error("Dataset upload failed:", error);
        const errorMessage =
            (error as { data?: { detail?: string }; message?: string })?.data?.detail ||
            (error as { message?: string })?.message ||
            "Failed to process dataset upload.";
        showStatus(errorMessage, "error");
    } finally {
        isProcessing.value = false;
    }
};

// Copy lock conflicts to clipboard as formatted JSON
const copyLockConflictsToClipboard = async () => {
    if (!lockConflicts.value || lockConflicts.value.length === 0) {
        showStatus("No lock conflicts to copy.", "error");
        return;
    }

    try {
        // Create a structured JSON object with detailed conflict information
        const conflictData = {
            summary: {
                total_conflicts: lockConflicts.value.length,
                total_locked_fields: lockConflicts.value.reduce(
                    (sum, conflict) => sum + Object.keys(conflict.locked_fields).length,
                    0,
                ),
                timestamp: new Date().toISOString(),
            },
            conflicts: lockConflicts.value.map((conflict, index) => ({
                entity_number: index + 1,
                entity_id: conflict.entity_id,
                entity_uuid: conflict.entity_uuid,
                entity_name: conflict.entity_data?.name || "Unknown",
                locked_fields: Object.entries(conflict.locked_fields).map(([fieldName, fieldInfo]) => ({
                    field_name: fieldName,
                    is_locked: fieldInfo.locked,
                    current_value: fieldInfo.current_value,
                    attempted_value: fieldInfo.attempted_value,
                    value_type_current: typeof fieldInfo.current_value,
                    value_type_attempted: typeof fieldInfo.attempted_value,
                })),
                entity_metadata: conflict.entity_data,
            })),
        };

        // Format as pretty JSON
        const jsonString = JSON.stringify(conflictData, null, 2);

        // Copy to clipboard
        await navigator.clipboard.writeText(jsonString);

        showStatus(`Copied ${lockConflicts.value.length} lock conflicts to clipboard as JSON.`, "success");
    } catch (error) {
        console.error("Failed to copy to clipboard:", error);
        showStatus("Failed to copy to clipboard. Check console for details.", "error");
    }
};
</script>
