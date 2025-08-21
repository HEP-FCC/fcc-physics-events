<template>
    <UDropdownMenu
        v-model:open="isOpen"
        :items="dropdownItems"
        :ui="{
            content: 'w-80 max-h-96 overflow-y-auto',
        }"
        @update:open="handleDropdownToggle"
    >
        <UButton icon="i-heroicons-tag" color="neutral" variant="outline" size="sm" class="cursor-pointer">
            Display Tags
            <template v-if="selectedFields.length > 0"> ({{ selectedFields.length }}) </template>
        </UButton>

        <template #item="{ item }">
            <div
                v-if="item.type === 'checkbox'"
                class="flex items-center w-full py-1 px-2 hover:bg-space-50 rounded cursor-pointer"
                @click.stop="handleFieldToggle(item.field)"
            >
                <UCheckbox
                    :model-value="isFieldSelected(item.field)"
                    size="sm"
                    class="mr-3"
                    @change.stop="handleFieldToggle(item.field)"
                    @click.stop
                />
                <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium truncate" style="max-width: 240px" :title="item.label">
                        {{ item.label }}
                    </div>
                </div>
            </div>
            <div v-else-if="item.type === 'label'" class="flex items-center w-full py-2 px-3 text-sm">
                {{ item.label }}
            </div>
        </template>

        <template #content-top>
            <div class="p-3 border-b border-space-200">
                <div class="flex items-start justify-between mb-2">
                    <h3 class="text-sm font-semibold">Select Metadata to Show as Tags</h3>
                    <UButton
                        icon="i-heroicons-x-mark"
                        color="neutral"
                        variant="ghost"
                        size="xs"
                        class="w-6 h-6 p-1 hover:bg-gray-100 rounded cursor-pointer flex items-center justify-center shrink-0"
                        @click="closeDropdown"
                    />
                </div>
                <p class="text-xs mb-3">
                    Choose which metadata fields to display as tags on all entities. Fields without data will show
                    "NONE" as the value.
                </p>

                <!-- Search input -->
                <div class="relative">
                    <UIcon
                        name="i-heroicons-magnifying-glass"
                        class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4"
                    />
                    <UInput v-model="searchQuery" placeholder="Search fields..." size="sm" class="pl-10" />
                </div>
            </div>
        </template>

        <template #content-bottom>
            <div class="p-3 border-t border-space-200 bg-space-50">
                <div class="flex items-center justify-between gap-2">
                    <div class="text-xs">{{ selectedFields.length }} of {{ availableFields.length }} selected</div>
                    <div class="flex gap-2">
                        <UButton
                            v-if="selectedFields.length > 0"
                            size="xs"
                            variant="ghost"
                            color="neutral"
                            @click.stop="handleClearAll"
                        >
                            Clear All
                        </UButton>
                        <UButton
                            v-if="selectedFields.length < availableFields.length"
                            size="xs"
                            variant="ghost"
                            color="primary"
                            @click.stop="handleSelectAll"
                        >
                            Select All
                        </UButton>
                    </div>
                </div>
            </div>
        </template>
    </UDropdownMenu>
</template>

<script setup lang="ts">
import type { Entity } from "~/types/entity";

interface Props {
    entities?: Entity[];
}

// Define dropdown item types
interface CheckboxItem {
    type: "checkbox";
    field: string;
    label: string;
}

interface LabelItem {
    type: "label";
    label: string;
    disabled?: boolean;
}

type DropdownItem = CheckboxItem | LabelItem;

const props = withDefaults(defineProps<Props>(), {
    entities: () => [],
});

// Composables
const {
    selectedFields,
    isFieldSelected,
    toggleField,
    clearAllFields,
    setSelectedFields,
    getAvailableFields,
    formatFieldName,
} = useMetadataPreferences();

// Local state
const searchQuery = ref("");
const isOpen = ref(false);

// Computed properties
const availableFields = computed(() => {
    return getAvailableFields(props.entities);
});

const filteredFields = computed(() => {
    if (!searchQuery.value.trim()) {
        return availableFields.value;
    }

    const query = searchQuery.value.toLowerCase();
    return availableFields.value.filter(
        (field) => field.toLowerCase().includes(query) || formatFieldName(field).toLowerCase().includes(query),
    );
});

const dropdownItems = computed(() => {
    const items: DropdownItem[] = [];

    // Add checkbox items for each field
    filteredFields.value.forEach((field) => {
        items.push({
            type: "checkbox" as const,
            field,
            label: formatFieldName(field),
        });
    });

    // If no results found, show a message
    if (filteredFields.value.length === 0 && searchQuery.value.trim()) {
        items.push({
            type: "label" as const,
            label: "No fields found",
            disabled: true,
        });
    }

    return [items];
});

// Methods
const handleDropdownToggle = (open: boolean) => {
    isOpen.value = open;
    if (open) {
        // Clear search when opening
        searchQuery.value = "";
    }
};

const closeDropdown = () => {
    isOpen.value = false;
};

const handleFieldToggle = (field: string) => {
    toggleField(field);
    // Don't close dropdown - let user continue selecting
};

const handleClearAll = () => {
    clearAllFields();
};

const handleSelectAll = () => {
    setSelectedFields([...availableFields.value]);
};
</script>

<style scoped>
.truncate {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
</style>
