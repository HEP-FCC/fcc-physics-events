<template>
    <div class="bg-white border-b border-gray-200 mb-6">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <nav class="flex space-x-8 py-4">
                <!-- Dynamic Navigation Dropdowns -->
                <template v-for="(type, index) in navigationOrder" :key="type">
                    <div
                        v-if="index === 0 || currentPath[navigationOrder[index - 1]]"
                        class="relative dropdown-container"
                    >
                        <UButton
                            :color="currentPath[type] ? 'primary' : 'neutral'"
                            :variant="currentPath[type] ? 'solid' : 'ghost'"
                            trailing-icon="i-heroicons-chevron-down-20-solid"
                            :loading="dropdowns[type].isLoading"
                            @click="handleToggleDropdown(type)"
                        >
                            <UIcon :name="dropdowns[type].icon" class="mr-2" />
                            {{ currentPath[type] || dropdowns[type].label }}
                        </UButton>

                        <div
                            v-if="dropdowns[type].isOpen"
                            class="absolute top-full left-0 mt-1 w-auto min-w-48 max-w-xs bg-white border border-gray-200 rounded-md shadow-lg z-50 dropdown-menu"
                        >
                            <div class="p-2">
                                <div v-if="currentPath[type]" class="mb-2">
                                    <button
                                        class="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-gray-50 rounded flex items-center whitespace-nowrap"
                                        @click="handleClearSelection(type)"
                                    >
                                        <UIcon name="i-heroicons-x-mark" class="mr-2" />
                                        {{ dropdowns[type].clearLabel }}
                                    </button>
                                </div>

                                <div v-if="dropdowns[type].isLoading" class="p-2">
                                    <USkeleton class="h-4 w-24" />
                                </div>

                                <div v-else class="space-y-1">
                                    <button
                                        v-for="item in dropdowns[type].items"
                                        :key="item.id"
                                        class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 rounded whitespace-nowrap"
                                        :class="{
                                            'bg-primary-50 text-primary-700': currentPath[type] === item.name,
                                        }"
                                        @click="handleNavigate(type, item.name)"
                                    >
                                        {{ item.name }}
                                    </button>
                                    <div v-if="!dropdowns[type].items.length" class="px-3 py-2 text-sm text-gray-500">
                                        No options available.
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </template>
            </nav>
        </div>
    </div>
</template>

<script setup lang="ts">
import { watchEffect, ref, onMounted, onUnmounted } from "vue";
import { useNavigationState } from "~/composables/useNavigationState";
import { useDynamicNavigation } from "~/composables/useDynamicNavigation";

interface Props {
    routeParams: string[];
}

const props = defineProps<Props>();

const {
    dropdowns,
    navigationOrder,
    loadDropdownData,
    toggleDropdown,
    closeAllDropdowns,
    clearDependentDropdowns,
    getItems,
    isLoading,
    isOpen,
} = useNavigationState();

const { parseRouteToPath, buildNavigationUrl, clearNavigationFrom } = useDynamicNavigation();

// Async navigation state
const currentPath = ref<Record<string, string | null>>({});

// Watch route params and update data asynchronously
watchEffect(() => {
    const params = props.routeParams;
    try {
        currentPath.value = parseRouteToPath(params);
    } catch (error) {
        console.error("Error parsing route to path:", error);
        currentPath.value = {};
    }
});

// Methods
function handleToggleDropdown(type: string) {
    toggleDropdown(type);

    // Only load data if dropdown is now open and has no data yet
    if (!isOpen(type)) {
        return;
    }

    // Check if data is already loaded or currently loading
    if (getItems(type).length > 0 || isLoading(type)) {
        return;
    }

    // Load data
    loadDropdownData(type);
}

function handleNavigate(type: string, value: string) {
    const newPath = buildNavigationUrl(currentPath.value, type, value);
    navigateTo(newPath);
    closeAllDropdowns();

    // Load filtered data for the next level
    const typeIndex = navigationOrder.findIndex((orderType) => orderType === type);
    if (typeIndex !== -1 && typeIndex < navigationOrder.length - 1) {
        const nextType = navigationOrder[typeIndex + 1];

        // Build filters up to this level
        const filters: Record<string, string> = {};
        for (let i = 0; i <= typeIndex; i++) {
            const filterType = navigationOrder[i];
            const filterValue = filterType === type ? value : currentPath.value[filterType];
            if (filterValue) {
                filters[filterType] = filterValue;
            }
        }

        // Clear dependent dropdowns first to show filtered results
        clearDependentDropdowns(type);
        loadDropdownData(nextType, filters, true); // Force reload with new filters
    }
}

function handleClearSelection(type: string) {
    const newPath = clearNavigationFrom(currentPath.value, type);
    navigateTo(newPath);
    closeAllDropdowns();

    // Clear dependent dropdowns and reload unfiltered data
    clearDependentDropdowns(type);

    // Reload data for the next level with updated filters
    const typeIndex = navigationOrder.findIndex((orderType) => orderType === type);
    if (typeIndex !== -1 && typeIndex < navigationOrder.length - 1) {
        const nextType = navigationOrder[typeIndex + 1];

        // Build filters up to the previous level (excluding the cleared level)
        const filters: Record<string, string> = {};
        for (let i = 0; i < typeIndex; i++) {
            const filterType = navigationOrder[i];
            const filterValue = currentPath.value[filterType];
            if (filterValue) {
                filters[filterType] = filterValue;
            }
        }

        loadDropdownData(nextType, filters, true); // Force reload with updated filters
    }
}

// Click outside handler
const handleClickOutside = (event: Event): void => {
    const target = event.target as HTMLElement;
    if (!target.closest(".dropdown-container")) {
        closeAllDropdowns();
    }
};

// Auto-load first level data on mount
onMounted(() => {
    // Load all dropdown data on mount for better UX
    navigationOrder.forEach((type, index) => {
        if (index === 0) {
            // Load first level immediately
            loadDropdownData(type);
        } else {
            // For subsequent levels, load with empty filters to get all options
            // This gives users a preview of what's available
            loadDropdownData(type);
        }
    });

    // Add click outside handler
    document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
    document.removeEventListener("click", handleClickOutside);
});

// Watch for changes in navigation path and auto-load dependent data
watchEffect(() => {
    navigationOrder.forEach((type, index) => {
        if (index === 0) return; // Skip first level - already loaded on mount

        // Check if all previous levels are selected
        const previousLevelsSelected = navigationOrder.slice(0, index).every((prevType) => currentPath.value[prevType]);

        if (previousLevelsSelected && currentPath.value[type]) {
            // Build filters for this level
            const filters: Record<string, string> = {};
            navigationOrder.slice(0, index).forEach((prevType) => {
                if (currentPath.value[prevType]) {
                    filters[prevType] = currentPath.value[prevType]!;
                }
            });

            // Load data if not already loaded
            if (getItems(type).length === 0 && !isLoading(type)) {
                loadDropdownData(type, filters);
            }
        }
    });
});
</script>
