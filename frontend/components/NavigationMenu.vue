<template>
    <div class="bg-white border-b border-gray-200 mb-6">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <nav class="flex space-x-8 py-4">
                <!-- Stage Dropdown -->
                <div class="relative dropdown-container">
                    <UButton
                        :color="currentPath.stage ? 'primary' : 'neutral'"
                        :variant="currentPath.stage ? 'solid' : 'ghost'"
                        trailing-icon="i-heroicons-chevron-down-20-solid"
                        :loading="dropdowns.stage.isLoading"
                        @click="handleToggleDropdown('stage')"
                    >
                        <UIcon name="i-heroicons-cpu-chip" class="mr-2" />
                        {{ currentPath.stage || "Stage" }}
                    </UButton>

                    <div
                        v-if="dropdowns.stage.isOpen"
                        class="absolute top-full left-0 mt-1 w-auto min-w-48 max-w-xs bg-white border border-gray-200 rounded-md shadow-lg z-50 dropdown-menu"
                    >
                        <div class="p-2">
                            <div v-if="currentPath.stage" class="mb-2">
                                <button
                                    class="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-gray-50 rounded flex items-center whitespace-nowrap"
                                    @click="handleClearSelection('stage')"
                                >
                                    <UIcon name="i-heroicons-x-mark" class="mr-2" />
                                    Clear Stage
                                </button>
                            </div>

                            <div v-if="dropdowns.stage.isLoading" class="p-2">
                                <USkeleton class="h-4 w-24" />
                            </div>

                            <div v-else class="space-y-1">
                                <button
                                    v-for="item in dropdowns.stage.items"
                                    :key="item.id"
                                    class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 rounded whitespace-nowrap"
                                    :class="{
                                        'bg-primary-50 text-primary-700': currentPath.stage === item.name,
                                    }"
                                    @click="handleNavigate('stage', item.name)"
                                >
                                    {{ item.name }}
                                </button>
                                <div v-if="!dropdowns.stage.items.length" class="px-3 py-2 text-sm text-gray-500">
                                    No options available.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Campaign Dropdown -->
                <div v-if="currentPath.stage" class="relative dropdown-container">
                    <UButton
                        :color="currentPath.campaign ? 'primary' : 'neutral'"
                        :variant="currentPath.campaign ? 'solid' : 'ghost'"
                        trailing-icon="i-heroicons-chevron-down-20-solid"
                        :loading="dropdowns.campaign.isLoading"
                        @click="handleToggleDropdown('campaign')"
                    >
                        <UIcon name="i-heroicons-calendar-days" class="mr-2" />
                        {{ currentPath.campaign || "Campaign" }}
                    </UButton>

                    <div
                        v-if="dropdowns.campaign.isOpen"
                        class="absolute top-full left-0 mt-1 w-auto min-w-48 max-w-xs bg-white border border-gray-200 rounded-md shadow-lg z-50 dropdown-menu"
                    >
                        <div class="p-2">
                            <div v-if="currentPath.campaign" class="mb-2">
                                <button
                                    class="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-gray-50 rounded flex items-center whitespace-nowrap"
                                    @click="handleClearSelection('campaign')"
                                >
                                    <UIcon name="i-heroicons-x-mark" class="mr-2" />
                                    Clear Campaign
                                </button>
                            </div>

                            <div v-if="dropdowns.campaign.isLoading" class="p-2">
                                <USkeleton class="h-4 w-24" />
                            </div>

                            <div v-else class="space-y-1">
                                <button
                                    v-for="item in dropdowns.campaign.items"
                                    :key="item.id"
                                    class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 rounded whitespace-nowrap"
                                    :class="{
                                        'bg-primary-50 text-primary-700': currentPath.campaign === item.name,
                                    }"
                                    @click="handleNavigate('campaign', item.name)"
                                >
                                    {{ item.name }}
                                </button>
                                <div v-if="!dropdowns.campaign.items.length" class="px-3 py-2 text-sm text-gray-500">
                                    No options available.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Detector Dropdown -->
                <div v-if="currentPath.stage && currentPath.campaign" class="relative dropdown-container">
                    <UButton
                        :color="currentPath.detector ? 'primary' : 'neutral'"
                        :variant="currentPath.detector ? 'solid' : 'ghost'"
                        trailing-icon="i-heroicons-chevron-down-20-solid"
                        :loading="dropdowns.detector.isLoading"
                        @click="handleToggleDropdown('detector')"
                    >
                        <UIcon name="i-heroicons-beaker" class="mr-2" />
                        {{ currentPath.detector || "Detector" }}
                    </UButton>

                    <div
                        v-if="dropdowns.detector.isOpen"
                        class="absolute top-full left-0 mt-1 w-auto min-w-48 max-w-xs bg-white border border-gray-200 rounded-md shadow-lg z-50 dropdown-menu"
                    >
                        <div class="p-2">
                            <div v-if="currentPath.detector" class="mb-2">
                                <button
                                    class="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-gray-50 rounded flex items-center whitespace-nowrap"
                                    @click="handleClearSelection('detector')"
                                >
                                    <UIcon name="i-heroicons-x-mark" class="mr-2" />
                                    Clear Detector
                                </button>
                            </div>

                            <div v-if="dropdowns.detector.isLoading" class="p-2">
                                <USkeleton class="h-4 w-24" />
                            </div>

                            <div v-else class="space-y-1">
                                <button
                                    v-for="item in dropdowns.detector.items"
                                    :key="item.id"
                                    class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 rounded whitespace-nowrap"
                                    :class="{
                                        'bg-primary-50 text-primary-700': currentPath.detector === item.name,
                                    }"
                                    @click="handleNavigate('detector', item.name)"
                                >
                                    {{ item.name }}
                                </button>
                                <div v-if="!dropdowns.detector.items.length" class="px-3 py-2 text-sm text-gray-500">
                                    No options available.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Navigation breadcrumbs -->
                <div class="flex items-center space-x-2 text-sm text-gray-500 ml-auto">
                    <span v-if="!Object.values(currentPath).some((v) => v)"> All Datasets </span>
                    <template v-else>
                        <span>Filtered by:</span>
                        <UBadge v-if="currentPath.stage" color="success" variant="soft">
                            Stage: {{ currentPath.stage }}
                        </UBadge>
                        <UBadge v-if="currentPath.campaign" color="warning" variant="soft">
                            Campaign: {{ currentPath.campaign }}
                        </UBadge>
                        <UBadge v-if="currentPath.detector" color="info" variant="soft">
                            Detector: {{ currentPath.detector }}
                        </UBadge>
                    </template>
                </div>
            </nav>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { DropdownType } from "~/types/dataset";
import { useNavigation } from "~/composables/useNavigation";

interface Props {
    routeParams: string[];
}

const props = defineProps<Props>();

const { dropdowns, loadDropdownData, toggleDropdown, closeAllDropdowns, clearDependentDropdowns } = useNavigation();

// We need these navigation helper functions from the old composable
function getCurrentPath(routeParams: string[]) {
    const dropdownKeys = ["stage", "campaign", "detector"] as const;
    const pathObj: Record<string, string | null> = {};
    dropdownKeys.forEach((type, index) => {
        pathObj[type] = routeParams[index] || null;
    });
    return pathObj;
}

function navigateToPath(type: DropdownType, value: string, currentPath: Record<string, string | null>) {
    const dropdownKeys = ["stage", "campaign", "detector"] as const;
    const pathParts = dropdownKeys.map((t) => currentPath[t]);
    const typeIndex = dropdownKeys.indexOf(type);

    const newPathParts = pathParts.slice(0, typeIndex);
    newPathParts.push(value);

    const newPath = `/${newPathParts.filter((p) => p).join("/")}`;
    navigateTo(newPath);
}

function clearSelectionPath(type: DropdownType, currentPath: Record<string, string | null>) {
    const dropdownKeys = ["stage", "campaign", "detector"] as const;
    const pathParts = dropdownKeys.map((t) => currentPath[t]);
    const typeIndex = dropdownKeys.indexOf(type);

    const newPathParts = pathParts.slice(0, typeIndex).filter((p) => p);
    const newPath = newPathParts.length === 0 ? "/" : `/${newPathParts.join("/")}`;
    navigateTo(newPath);
}

// Computed properties
const currentPath = computed(() => getCurrentPath(props.routeParams));

// Methods
function handleToggleDropdown(type: DropdownType) {
    toggleDropdown(type);

    // Only load data if dropdown is now open and has no data yet
    if (!dropdowns.value[type].isOpen) return;

    // Check if data is already loaded or currently loading
    if (dropdowns.value[type].items.length > 0 || dropdowns.value[type].isLoading) return;

    // Load data based on dropdown type and current path
    if (type === "stage") {
        loadDropdownData("stage", {});
    } else if (type === "campaign") {
        // Load campaigns filtered by current stage
        const filters: Record<string, string> = {};
        if (currentPath.value.stage) filters.stage_name = currentPath.value.stage;
        loadDropdownData("campaign", filters);
    } else if (type === "detector") {
        // Load detectors filtered by current stage and campaign
        const filters: Record<string, string> = {};
        if (currentPath.value.stage) filters.stage_name = currentPath.value.stage;
        if (currentPath.value.campaign) filters.campaign_name = currentPath.value.campaign;
        loadDropdownData("detector", filters);
    }
}

function handleNavigate(type: DropdownType, value: string) {
    // Clear dependent dropdowns when navigating to a higher level
    clearDependentDropdowns(type);

    navigateToPath(type, value, currentPath.value);
    closeAllDropdowns();
}

function handleClearSelection(type: DropdownType) {
    // Clear dependent dropdowns when clearing a selection
    clearDependentDropdowns(type);

    clearSelectionPath(type, currentPath.value);
    closeAllDropdowns();
}

// Click outside handler
const handleClickOutside = (event: Event): void => {
    const target = event.target as HTMLElement;
    if (!target.closest(".dropdown-container")) {
        closeAllDropdowns();
    }
};

// Watch for path changes to reload dependent dropdowns
watch(
    () => currentPath.value,
    async (newPath, oldPath) => {
        // If stage changed, reload campaigns and clear detectors
        if (newPath.stage !== oldPath?.stage) {
            clearDependentDropdowns("stage");

            if (newPath.stage) {
                const stageFilters = { stage_name: newPath.stage };
                await loadDropdownData("campaign", stageFilters, true);
            }
        }

        // If campaign changed, reload detectors
        if (newPath.campaign !== oldPath?.campaign) {
            clearDependentDropdowns("campaign");

            if (newPath.stage && newPath.campaign) {
                const detectorFilters = {
                    stage_name: newPath.stage,
                    campaign_name: newPath.campaign,
                };
                await loadDropdownData("detector", detectorFilters, true);
            }
        }
    },
    { immediate: false },
);

// Component lifecycle
onMounted(async () => {
    document.addEventListener("click", handleClickOutside);

    // Pre-load all dropdown data on mount for better UX
    // Load stages first (no dependencies)
    await loadDropdownData("stage", {});

    // If we have a current stage, pre-load campaigns for that stage
    if (currentPath.value.stage) {
        const stageFilters = { stage_name: currentPath.value.stage };
        await loadDropdownData("campaign", stageFilters);

        // If we also have a campaign, pre-load detectors
        if (currentPath.value.campaign) {
            const detectorFilters = {
                stage_name: currentPath.value.stage,
                campaign_name: currentPath.value.campaign,
            };
            await loadDropdownData("detector", detectorFilters);
        }
    }
});

onUnmounted(() => {
    document.removeEventListener("click", handleClickOutside);
});
</script>
