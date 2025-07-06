<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import type { DropdownItem, DropdownType } from "../types/navigation";
import { useNavigationConfig, type NavigationDropdownConfig } from "../composables/useNavigationConfig";

const route = useRoute();
const router = useRouter();

const { navigationConfig, dropdownKeys, parseCurrentPath } = useNavigationConfig();

// Create reactive dropdowns from navigation config
const dropdowns = ref<Record<DropdownType, NavigationDropdownConfig>>(
    Object.fromEntries(
        Object.entries(navigationConfig).map(([key, config]) => [
            key,
            {
                ...config,
                items: [] as DropdownItem[],
                isLoading: false,
                isOpen: false,
            },
        ]),
    ) as Record<DropdownType, NavigationDropdownConfig>,
);

// Track loading timeouts for cleanup
const loadingTimeouts = ref<Map<DropdownType, NodeJS.Timeout>>(new Map());

const currentPath = computed(() => {
    const params = Array.isArray(route.params.slug) ? route.params.slug : [];
    return parseCurrentPath(params);
});

// Build navigation path for a dropdown selection
function buildNavigationPath(type: DropdownType, value: string): string {
    const current = currentPath.value;
    const pathParts = dropdownKeys.value.map((t) => current[t]);
    const typeIndex = dropdownKeys.value.indexOf(type);

    // Create path up to the selected type, then add the new value
    const newPathParts = pathParts.slice(0, typeIndex);
    newPathParts.push(value);

    return `/${newPathParts.filter((p) => p).join("/")}`;
}

function navigateTo(type: DropdownType, value: string) {
    const newPath = buildNavigationPath(type, value);
    router.push(newPath);
}

function clearSelection(type: DropdownType) {
    const current = currentPath.value;
    const pathParts = dropdownKeys.value.map((t) => current[t]);
    const typeIndex = dropdownKeys.value.indexOf(type);

    // Create path excluding the cleared type and everything after it
    const newPathParts = pathParts.slice(0, typeIndex).filter((p) => p);
    const newPath = newPathParts.length === 0 ? "/" : `/${newPathParts.join("/")}`;
    router.push(newPath);
}

function closeAllDropdowns() {
    Object.values(dropdowns.value).forEach((d) => (d.isOpen = false));
}

function getBadgeColor(type: DropdownType): "success" | "warning" | "info" | "primary" {
    switch (type) {
        case "stage":
            return "success"; // Green to match Stage badges in results
        case "campaign":
            return "warning"; // Yellow/amber to match Campaign badges in results
        case "detector":
            return "info"; // Blue to match Detector badges in results
        default:
            return "primary"; // Fallback color
    }
}

function toggleDropdown(type: DropdownType) {
    const wasOpen = dropdowns.value[type].isOpen;
    closeAllDropdowns();
    if (!wasOpen) {
        dropdowns.value[type].isOpen = true;
    }
}

function handleClickOutside(event: Event) {
    const target = event.target as HTMLElement;
    if (!target.closest(".relative")) {
        closeAllDropdowns();
    }
}

// Helper function to build filters for a specific dropdown type
function buildFiltersForDropdown(targetType: DropdownType): Record<string, string> {
    const current = currentPath.value;
    const filters: Record<string, string> = {};

    // Add filters for all other dropdown types
    for (const type of dropdownKeys.value) {
        if (type !== targetType && current[type]) {
            const filterKey = `${type}_name`;
            filters[filterKey] = current[type];
        }
    }

    return filters;
}

async function loadDropdownData() {
    // Clear any existing timeouts first
    loadingTimeouts.value.forEach((timeout) => clearTimeout(timeout));
    loadingTimeouts.value.clear();

    for (const type in dropdowns.value) {
        const dropdown = dropdowns.value[type as DropdownType];

        // Set up delayed loading - only show spinner after 2 seconds
        const loadingTimeout = setTimeout(() => {
            dropdown.isLoading = true;
        }, 2000);

        // Store timeout for cleanup
        loadingTimeouts.value.set(type as DropdownType, loadingTimeout);

        try {
            const filters = buildFiltersForDropdown(type as DropdownType);
            dropdown.items = await dropdown.apiCall(filters);
        } catch (error) {
            console.error(`Failed to load ${type}s:`, error);
            dropdown.items = [];
        } finally {
            // Clear the timeout and reset loading state
            clearTimeout(loadingTimeout);
            loadingTimeouts.value.delete(type as DropdownType);
            dropdown.isLoading = false;
        }
    }
}

onMounted(() => {
    loadDropdownData();
    document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
    document.removeEventListener("click", handleClickOutside);
    // Clean up any pending loading timeouts
    loadingTimeouts.value.forEach((timeout) => clearTimeout(timeout));
    loadingTimeouts.value.clear();
});

watch(currentPath, loadDropdownData, { deep: true });
</script>

<template>
    <div class="bg-white border-b border-gray-200 mb-6">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <nav class="flex space-x-8 py-4">
                <!-- Dynamic Dropdowns -->
                <div v-for="(dropdown, type) in dropdowns" :key="type" class="relative">
                    <UButton
                        :color="currentPath[type as DropdownType] ? 'primary' : 'neutral'"
                        :variant="currentPath[type as DropdownType] ? 'solid' : 'ghost'"
                        trailing-icon="i-heroicons-chevron-down-20-solid"
                        :loading="dropdown.isLoading"
                        @click="toggleDropdown(type as DropdownType)"
                    >
                        <UIcon :name="dropdown.icon" class="mr-2" />
                        {{ currentPath[type as DropdownType] || dropdown.label }}
                    </UButton>

                    <div
                        v-if="dropdown.isOpen"
                        class="absolute top-full left-0 mt-1 w-auto min-w-48 max-w-xs bg-white border border-gray-200 rounded-md shadow-lg z-50"
                    >
                        <div class="p-2">
                            <div v-if="currentPath[type as DropdownType]" class="mb-2">
                                <button
                                    class="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-gray-50 rounded flex items-center whitespace-nowrap"
                                    @click="
                                        clearSelection(type as DropdownType);
                                        dropdown.isOpen = false;
                                    "
                                >
                                    <UIcon name="i-heroicons-x-mark" class="mr-2" />
                                    {{ dropdown.clearLabel }}
                                </button>
                            </div>

                            <div v-if="dropdown.isLoading" class="p-2">
                                <USkeleton class="h-4 w-24" />
                            </div>

                            <div v-else class="space-y-1">
                                <button
                                    v-for="item in dropdown.items"
                                    :key="item.id"
                                    class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 rounded whitespace-nowrap"
                                    :class="{
                                        'bg-primary-50 text-primary-700':
                                            currentPath[type as DropdownType] === item.name,
                                    }"
                                    @click="
                                        navigateTo(type as DropdownType, item.name);
                                        dropdown.isOpen = false;
                                    "
                                >
                                    {{ item.name }}
                                </button>
                                <div v-if="!dropdown.items.length" class="px-3 py-2 text-sm text-gray-500">
                                    No options available.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Current Path Breadcrumb -->
                <div class="flex items-center space-x-2 text-sm text-gray-500 ml-auto">
                    <span v-if="!Object.values(currentPath).some((v) => v)"> All Datasets </span>
                    <template v-else>
                        <span>Filtered by:</span>
                        <template v-for="(dropdown, type) in dropdowns" :key="type">
                            <UBadge
                                v-if="currentPath[type as DropdownType]"
                                :color="getBadgeColor(type as DropdownType)"
                                variant="soft"
                            >
                                {{ dropdown.label }}: {{ currentPath[type as DropdownType] }}
                            </UBadge>
                        </template>
                    </template>
                </div>
            </nav>
        </div>
    </div>
</template>
