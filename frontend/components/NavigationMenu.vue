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

const currentPath = computed(() => {
    const params = Array.isArray(route.params.slug) ? route.params.slug : [];
    return parseCurrentPath(params);
});

function navigateTo(type: DropdownType, value: string) {
    const current = currentPath.value;
    // Create pathParts array in the correct order
    const pathParts = dropdownKeys.value.map((t) => current[t]);
    const typeIndex = dropdownKeys.value.indexOf(type);

    // Create a new path up to the selected type
    const newPathParts = pathParts.slice(0, typeIndex);
    newPathParts.push(value);

    // Filter out nulls and join to form the path
    const newPath = `/${newPathParts.filter((p) => p).join("/")}`;
    router.push(newPath);
}

function clearSelection(type: DropdownType) {
    const current = currentPath.value;
    // Create pathParts array in the correct order
    const pathParts = dropdownKeys.value.map((t) => current[t]);
    const typeIndex = dropdownKeys.value.indexOf(type);

    // Create a new path that excludes the cleared type and everything after it
    const newPathParts = pathParts.slice(0, typeIndex);

    if (newPathParts.length === 0) {
        router.push("/");
    } else {
        const newPath = `/${newPathParts.filter((p) => p).join("/")}`;
        router.push(newPath);
    }
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

async function loadDropdownData() {
    const current = currentPath.value;

    // Dynamically generate filter map based on dropdowns configuration order
    const filterMap = {} as Record<DropdownType, Record<string, unknown>>;
    for (const type of dropdownKeys.value) {
        filterMap[type] = {};
        // Add filters for all other dropdown types
        for (const otherType of dropdownKeys.value) {
            if (otherType !== type) {
                const filterKey = `${otherType}_name`;
                filterMap[type][filterKey] = current[otherType];
            }
        }
    }

    for (const type in dropdowns.value) {
        const dropdown = dropdowns.value[type as DropdownType];
        dropdown.isLoading = true;
        try {
            const filters = Object.fromEntries(
                Object.entries(filterMap[type as DropdownType]).filter(([_, v]) => v != null),
            );
            dropdown.items = await dropdown.apiCall(filters);
        } catch (error) {
            console.error(`Failed to load ${type}s:`, error);
            dropdown.items = [];
        } finally {
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
                                    :class="{ 'bg-primary-50 text-primary-700': currentPath[type as DropdownType] === item.name }"
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
