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

                <!-- Accelerator Dropdown -->
                <div v-if="currentPath.stage" class="relative dropdown-container">
                    <UButton
                        :color="currentPath.accelerator ? 'primary' : 'neutral'"
                        :variant="currentPath.accelerator ? 'solid' : 'ghost'"
                        trailing-icon="i-heroicons-chevron-down-20-solid"
                        :loading="dropdowns.accelerator.isLoading"
                        @click="handleToggleDropdown('accelerator')"
                    >
                        <UIcon name="i-heroicons-bolt" class="mr-2" />
                        {{ currentPath.accelerator || "Accelerator" }}
                    </UButton>

                    <div
                        v-if="dropdowns.accelerator.isOpen"
                        class="absolute top-full left-0 mt-1 w-auto min-w-48 max-w-xs bg-white border border-gray-200 rounded-md shadow-lg z-50 dropdown-menu"
                    >
                        <div class="p-2">
                            <div v-if="currentPath.accelerator" class="mb-2">
                                <button
                                    class="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-gray-50 rounded flex items-center whitespace-nowrap"
                                    @click="handleClearSelection('accelerator')"
                                >
                                    <UIcon name="i-heroicons-x-mark" class="mr-2" />
                                    Clear Accelerator
                                </button>
                            </div>

                            <div v-if="dropdowns.accelerator.isLoading" class="p-2">
                                <USkeleton class="h-4 w-24" />
                            </div>

                            <div v-else class="space-y-1">
                                <button
                                    v-for="item in dropdowns.accelerator.items"
                                    :key="item.id"
                                    class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 rounded whitespace-nowrap"
                                    :class="{
                                        'bg-primary-50 text-primary-700': currentPath.accelerator === item.name,
                                    }"
                                    @click="handleNavigate('accelerator', item.name)"
                                >
                                    {{ item.name }}
                                </button>
                                <div v-if="!dropdowns.accelerator.items.length" class="px-3 py-2 text-sm text-gray-500">
                                    No options available.
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Campaign Dropdown -->
                <div v-if="currentPath.stage && currentPath.accelerator" class="relative dropdown-container">
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
                <div
                    v-if="currentPath.stage && currentPath.accelerator && currentPath.campaign"
                    class="relative dropdown-container"
                >
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
            </nav>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { DropdownType } from "~/types/dataset";
import { useNavigation } from "~/composables/useNavigation";
import { parseRouteToPath, buildNavigationPath, buildClearPath, NAVIGATION_CONFIG } from "~/config/navigation";

interface Props {
    routeParams: string[];
}

const props = defineProps<Props>();

const { dropdowns, loadDropdownData, toggleDropdown, closeAllDropdowns, clearDependentDropdowns } = useNavigation();

// Computed properties
const currentPath = computed(() => parseRouteToPath(props.routeParams));

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
    } else if (type === "accelerator") {
        // Load accelerators filtered by current stage
        const filters: Record<string, string> = {};
        if (currentPath.value.stage) filters.stage_name = currentPath.value.stage;
        loadDropdownData("accelerator", filters);
    } else if (type === "campaign") {
        // Load campaigns filtered by current stage and accelerator
        const filters: Record<string, string> = {};
        if (currentPath.value.stage) filters.stage_name = currentPath.value.stage;
        if (currentPath.value.accelerator) filters.accelerator_name = currentPath.value.accelerator;
        loadDropdownData("campaign", filters);
    } else if (type === "detector") {
        // Load detectors filtered by current stage, accelerator and campaign
        const filters: Record<string, string> = {};
        if (currentPath.value.stage) filters.stage_name = currentPath.value.stage;
        if (currentPath.value.accelerator) filters.accelerator_name = currentPath.value.accelerator;
        if (currentPath.value.campaign) filters.campaign_name = currentPath.value.campaign;
        loadDropdownData("detector", filters);
    }
}

function handleNavigate(type: DropdownType, value: string) {
    // Clear dependent dropdowns when navigating to a higher level
    clearDependentDropdowns(type);

    const newPath = buildNavigationPath(currentPath.value, type, value);
    navigateTo(newPath);
    closeAllDropdowns();
}

function handleClearSelection(type: DropdownType) {
    // Clear dependent dropdowns when clearing a selection
    clearDependentDropdowns(type);

    const newPath = buildClearPath(currentPath.value, type);
    navigateTo(newPath);
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
        // If stage changed, reload accelerators and clear dependent dropdowns
        if (newPath.stage !== oldPath?.stage) {
            clearDependentDropdowns("stage");

            if (newPath.stage) {
                const stageFilters = { stage_name: newPath.stage };
                await loadDropdownData("accelerator", stageFilters, true);
            }
        }

        // If accelerator changed, reload campaigns and clear detectors
        if (newPath.accelerator !== oldPath?.accelerator) {
            clearDependentDropdowns("accelerator");

            if (newPath.stage && newPath.accelerator) {
                const acceleratorFilters = {
                    stage_name: newPath.stage,
                    accelerator_name: newPath.accelerator,
                };
                await loadDropdownData("campaign", acceleratorFilters, true);
            }
        }

        // If campaign changed, reload detectors
        if (newPath.campaign !== oldPath?.campaign) {
            clearDependentDropdowns("campaign");

            if (newPath.stage && newPath.accelerator && newPath.campaign) {
                const detectorFilters = {
                    stage_name: newPath.stage,
                    accelerator_name: newPath.accelerator,
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

    // If we have a current stage, pre-load accelerators for that stage
    if (currentPath.value.stage) {
        const stageFilters = { stage_name: currentPath.value.stage };
        await loadDropdownData("accelerator", stageFilters);

        // If we also have an accelerator, pre-load campaigns
        if (currentPath.value.accelerator) {
            const acceleratorFilters = {
                stage_name: currentPath.value.stage,
                accelerator_name: currentPath.value.accelerator,
            };
            await loadDropdownData("campaign", acceleratorFilters);

            // If we also have a campaign, pre-load detectors
            if (currentPath.value.campaign) {
                const detectorFilters = {
                    stage_name: currentPath.value.stage,
                    accelerator_name: currentPath.value.accelerator,
                    campaign_name: currentPath.value.campaign,
                };
                await loadDropdownData("detector", detectorFilters);
            }
        }
    }
});

onUnmounted(() => {
    document.removeEventListener("click", handleClickOutside);
});
</script>
