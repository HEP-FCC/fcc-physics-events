<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import { useRouter } from "vue-router";
import { loadingDelay } from "~/composables/loadingDelay";
import type { DropdownItem } from "~/types/navigation";
import { navigationConfig, type NavigationDropdownConfig, type DropdownType } from "~/composables/navigationConfig";

interface Props {
    routeParams?: string[];
}

const props = withDefaults(defineProps<Props>(), {
    routeParams: () => [],
});

const router = useRouter();

const { navigationConfig: navConfig, dropdownKeys, parseCurrentPath, getVisibleDropdowns } = navigationConfig();

// Create reactive dropdowns from navigation config
const dropdowns = ref<Record<DropdownType, NavigationDropdownConfig>>(
    Object.fromEntries(
        Object.entries(navConfig).map(([key, config]) => [
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

// Use loading delay utility for smoother UX (shorter delay for navigation dropdowns)
const loadingDelayMap = new Map<DropdownType, ReturnType<typeof loadingDelay>>();

// Initialize loading delay for each dropdown type with a reasonable delay
Object.keys(dropdowns.value).forEach((type) => {
    loadingDelayMap.set(type as DropdownType, loadingDelay({ delayMs: 500 }));
});

const currentPath = computed(() => {
    return parseCurrentPath(props.routeParams);
});

// Get visible dropdowns based on current selections
const visibleDropdowns = computed(() => {
    return getVisibleDropdowns(currentPath.value);
});

// Filter dropdowns to only show visible ones
const activeDropdowns = computed(() => {
    const filtered: Record<DropdownType, NavigationDropdownConfig> = {} as Record<
        DropdownType,
        NavigationDropdownConfig
    >;

    visibleDropdowns.value.forEach((type) => {
        if (dropdowns.value[type]) {
            filtered[type] = dropdowns.value[type];
        }
    });

    return filtered;
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
    visibleDropdowns.value.forEach((type) => {
        if (dropdowns.value[type]) {
            dropdowns.value[type].isOpen = false;
        }
    });
}

function getBadgeColor(type: DropdownType): "success" | "warning" | "info" | "primary" {
    const colorMap: Record<DropdownType, "success" | "warning" | "info"> = {
        stage: "success", // Green to match Stage badges in results
        campaign: "warning", // Yellow/amber to match Campaign badges in results
        detector: "info", // Blue to match Detector badges in results
    };
    return colorMap[type] || "primary";
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
            filters[`${type}_name`] = current[type];
        }
    }

    return filters;
}

// Load dropdown data for visible dropdown types with improved loading states
async function loadDropdownData() {
    const loadPromises = visibleDropdowns.value.map(async (type) => {
        const dropdown = dropdowns.value[type];
        const loadingState = loadingDelayMap.get(type);

        if (!loadingState || !dropdown) return;

        loadingState.startLoading();

        // Set dropdown loading state when delay threshold is reached
        const stopWatching = watch(
            loadingState.shouldShowLoading,
            (shouldShow) => {
                dropdown.isLoading = shouldShow;
            },
            { immediate: true },
        );

        try {
            const filters = buildFiltersForDropdown(type);
            dropdown.items = await dropdown.apiCall(filters);
        } catch (error) {
            console.error(`Failed to load ${type}s:`, error);
            dropdown.items = [];
        } finally {
            loadingState.stopLoading();
            stopWatching(); // Clean up the watcher
        }
    });

    // Load all visible dropdowns in parallel for better performance
    await Promise.allSettled(loadPromises);
}

onMounted(() => {
    loadDropdownData();
    document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
    document.removeEventListener("click", handleClickOutside);
    // Cleanup is handled by loadingDelay composable
});

watch(currentPath, loadDropdownData, { deep: true });
watch(visibleDropdowns, loadDropdownData, { deep: true });
</script>

<template>
    <div class="bg-white border-b border-gray-200 mb-6">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <nav class="flex space-x-8 py-4">
                <!-- Dynamic Dropdowns - Progressive Navigation -->
                <div v-for="(dropdown, type) in activeDropdowns" :key="type" class="relative">
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
                        <template v-for="(dropdown, type) in activeDropdowns" :key="type">
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
