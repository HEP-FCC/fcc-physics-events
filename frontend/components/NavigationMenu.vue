<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { getApiClient, type DropdownItem } from "../composables/getApiClient";
import type { DropdownMenuItem } from "@nuxt/ui";

const route = useRoute();
const router = useRouter();
const apiClient = getApiClient();

// Reactive state for dropdown data
const dropdownData = ref<{
    frameworks: DropdownItem[];
    campaigns: DropdownItem[];
    detectors: DropdownItem[];
}>({
    frameworks: [],
    campaigns: [],
    detectors: [],
});

const isLoading = ref<{
    frameworks: boolean;
    campaigns: boolean;
    detectors: boolean;
}>({
    frameworks: true,
    campaigns: true,
    detectors: true,
});

// Get current active selections from the route
const currentSelection = computed(() => {
    const params = route.params.slug || [];
    return {
        framework: params[0] || null,
        campaign: params[1] || null,
        detector: params[2] || null,
    };
});

// Create dropdown items for UI
const frameworkItems = computed((): DropdownMenuItem[][] => {
    const items: DropdownMenuItem[][] = [
        [
            {
                label: "All Frameworks",
                icon: "i-heroicons-home",
                onSelect: () => navigateToPath(null, currentSelection.value.campaign, currentSelection.value.detector),
            },
        ],
    ];

    if (dropdownData.value.frameworks.length > 0) {
        items.push(
            dropdownData.value.frameworks.map((framework) => ({
                label: framework.name,
                icon: "i-heroicons-cpu-chip",
                onSelect: () =>
                    navigateToPath(framework.name, currentSelection.value.campaign, currentSelection.value.detector),
            })),
        );
    } else if (!isLoading.value.frameworks) {
        items.push([
            {
                label: "No frameworks available",
                disabled: true,
                icon: "i-heroicons-exclamation-triangle",
            },
        ]);
    }

    return items;
});

const campaignItems = computed((): DropdownMenuItem[][] => {
    const items: DropdownMenuItem[][] = [
        [
            {
                label: "All Campaigns",
                icon: "i-heroicons-home",
                onSelect: () => navigateToPath(currentSelection.value.framework, null, currentSelection.value.detector),
            },
        ],
    ];

    if (dropdownData.value.campaigns.length > 0) {
        items.push(
            dropdownData.value.campaigns.map((campaign) => ({
                label: campaign.name,
                icon: "i-heroicons-calendar",
                onSelect: () =>
                    navigateToPath(currentSelection.value.framework, campaign.name, currentSelection.value.detector),
            })),
        );
    } else if (!isLoading.value.campaigns) {
        const message = currentSelection.value.framework
            ? `No campaigns for ${currentSelection.value.framework}`
            : "No campaigns available";
        items.push([
            {
                label: message,
                disabled: true,
                icon: "i-heroicons-exclamation-triangle",
            },
        ]);
    }

    return items;
});

const detectorItems = computed((): DropdownMenuItem[][] => {
    const items: DropdownMenuItem[][] = [
        [
            {
                label: "All Detectors",
                icon: "i-heroicons-home",
                onSelect: () => navigateToPath(currentSelection.value.framework, currentSelection.value.campaign, null),
            },
        ],
    ];

    if (dropdownData.value.detectors.length > 0) {
        items.push(
            dropdownData.value.detectors.map((detector) => ({
                label: detector.name,
                icon: "i-heroicons-eye",
                onSelect: () =>
                    navigateToPath(currentSelection.value.framework, currentSelection.value.campaign, detector.name),
            })),
        );
    } else if (!isLoading.value.detectors) {
        let message = "No detectors available";
        if (currentSelection.value.framework && currentSelection.value.campaign) {
            message = `No detectors for ${currentSelection.value.framework}/${currentSelection.value.campaign}`;
        } else if (currentSelection.value.framework) {
            message = `No detectors for ${currentSelection.value.framework}`;
        }
        items.push([
            {
                label: message,
                disabled: true,
                icon: "i-heroicons-exclamation-triangle",
            },
        ]);
    }

    return items;
});

// Navigation function
function navigateToPath(framework: string | null, campaign: string | null, detector: string | null) {
    const pathSegments = [];

    if (framework) pathSegments.push(framework);
    if (campaign) pathSegments.push(campaign);
    if (detector) pathSegments.push(detector);

    const path = pathSegments.length > 0 ? `/${pathSegments.join("/")}` : "/";
    router.push(path);
}

// Clear all selections
function clearAllSelections() {
    router.push("/");
}

// Fetch frameworks (always unfiltered as it's the first level)
async function fetchFrameworks() {
    isLoading.value.frameworks = true;
    try {
        dropdownData.value.frameworks = await apiClient.getFrameworks();
    } catch (error) {
        console.error("Failed to fetch frameworks:", error);
        // Fallback to hardcoded data
        dropdownData.value.frameworks = [
            { id: 1, name: "Delphes" },
            { id: 2, name: "DD4hep" },
            { id: 3, name: "Gaudi" },
        ];
    } finally {
        isLoading.value.frameworks = false;
    }
}

// Fetch campaigns filtered by selected framework
async function fetchCampaigns() {
    isLoading.value.campaigns = true;
    try {
        const filters: any = {};
        if (currentSelection.value.framework) {
            filters.framework_name = currentSelection.value.framework;
        }

        dropdownData.value.campaigns = await apiClient.getCampaigns(filters);
    } catch (error) {
        console.error("Failed to fetch campaigns:", error);
        // Fallback to hardcoded data
        dropdownData.value.campaigns = [
            { id: 1, name: "winter2023" },
            { id: 2, name: "spring2024" },
            { id: 3, name: "summer2024" },
        ];
    } finally {
        isLoading.value.campaigns = false;
    }
}

// Fetch detectors filtered by selected framework and campaign
async function fetchDetectors() {
    isLoading.value.detectors = true;
    try {
        const filters: any = {};
        if (currentSelection.value.framework) {
            filters.framework_name = currentSelection.value.framework;
        }
        if (currentSelection.value.campaign) {
            filters.campaign_name = currentSelection.value.campaign;
        }

        dropdownData.value.detectors = await apiClient.getDetectors(filters);
    } catch (error) {
        console.error("Failed to fetch detectors:", error);
        // Fallback to hardcoded data
        dropdownData.value.detectors = [
            { id: 1, name: "IDEA" },
            { id: 2, name: "CLD" },
            { id: 3, name: "ALLEGRO" },
        ];
    } finally {
        isLoading.value.detectors = false;
    }
}

// Fetch all dropdown data in the correct order
async function fetchDropdownData() {
    // Always fetch frameworks first (unfiltered)
    await fetchFrameworks();
    // Fetch campaigns filtered by framework
    await fetchCampaigns();
    // Fetch detectors filtered by framework and campaign
    await fetchDetectors();
}

// Get button variants based on active state
function getButtonVariant(isActive: boolean) {
    return isActive ? "solid" : "outline";
}

function getButtonColor(isActive: boolean) {
    return isActive ? "primary" : "neutral";
}

// Get display text for buttons
const frameworkDisplayText = computed(() => {
    if (currentSelection.value.framework) {
        const framework = dropdownData.value.frameworks.find((f) => f.name === currentSelection.value.framework);
        return framework?.name || currentSelection.value.framework;
    }
    return "Framework";
});

const campaignDisplayText = computed(() => {
    if (currentSelection.value.campaign) {
        const campaign = dropdownData.value.campaigns.find((c) => c.name === currentSelection.value.campaign);
        return campaign?.name || currentSelection.value.campaign;
    }
    return "Campaign";
});

const detectorDisplayText = computed(() => {
    if (currentSelection.value.detector) {
        const detector = dropdownData.value.detectors.find((d) => d.name === currentSelection.value.detector);
        return detector?.name || currentSelection.value.detector;
    }
    return "Detector";
});

// Check if any filters are active
const hasActiveFilters = computed(() => {
    return !!(currentSelection.value.framework || currentSelection.value.campaign || currentSelection.value.detector);
});

// Fetch data on mount
onMounted(() => {
    fetchDropdownData();
});

// Watch for changes in the current selection to refetch dependent dropdowns
watch(
    () => currentSelection.value.framework,
    async (newFramework, oldFramework) => {
        if (newFramework !== oldFramework) {
            // When framework changes, refetch campaigns and detectors
            await fetchCampaigns();
            await fetchDetectors();
        }
    },
);

watch(
    () => currentSelection.value.campaign,
    async (newCampaign, oldCampaign) => {
        if (newCampaign !== oldCampaign) {
            // When campaign changes, refetch detectors
            await fetchDetectors();
        }
    },
);
</script>

<template>
    <div
        class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-gray-200"
    >
        <!-- Navigation Dropdowns -->
        <div class="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            <div class="text-sm font-medium text-gray-700 hidden sm:block">
                Filter by:
                <span class="text-xs text-gray-500 font-normal ml-1">(left to right)</span>
            </div>

            <div class="flex flex-wrap items-center gap-2">
                <!-- Framework Dropdown -->
                <UDropdownMenu :items="frameworkItems" :content="{ align: 'start' }" :ui="{ content: 'w-48' }">
                    <UButton
                        :variant="getButtonVariant(!!currentSelection.framework)"
                        :color="getButtonColor(!!currentSelection.framework)"
                        :loading="isLoading.frameworks"
                        trailing-icon="i-heroicons-chevron-down-20-solid"
                        size="sm"
                    >
                        {{ frameworkDisplayText }}
                    </UButton>
                </UDropdownMenu>

                <!-- Campaign Dropdown -->
                <UDropdownMenu :items="campaignItems" :content="{ align: 'start' }" :ui="{ content: 'w-48' }">
                    <UButton
                        :variant="getButtonVariant(!!currentSelection.campaign)"
                        :color="getButtonColor(!!currentSelection.campaign)"
                        :loading="isLoading.campaigns"
                        trailing-icon="i-heroicons-chevron-down-20-solid"
                        size="sm"
                        :disabled="isLoading.campaigns"
                    >
                        <template v-if="isLoading.campaigns">
                            <UIcon name="i-heroicons-arrow-path" class="animate-spin mr-1" />
                        </template>
                        {{ campaignDisplayText }}
                    </UButton>
                </UDropdownMenu>

                <!-- Detector Dropdown -->
                <UDropdownMenu :items="detectorItems" :content="{ align: 'start' }" :ui="{ content: 'w-48' }">
                    <UButton
                        :variant="getButtonVariant(!!currentSelection.detector)"
                        :color="getButtonColor(!!currentSelection.detector)"
                        :loading="isLoading.detectors"
                        trailing-icon="i-heroicons-chevron-down-20-solid"
                        size="sm"
                        :disabled="isLoading.detectors"
                    >
                        <template v-if="isLoading.detectors">
                            <UIcon name="i-heroicons-arrow-path" class="animate-spin mr-1" />
                        </template>
                        {{ detectorDisplayText }}
                    </UButton>
                </UDropdownMenu>
            </div>
        </div>

        <!-- Clear Filters Button -->
        <div class="flex items-center gap-2">
            <UButton
                v-if="hasActiveFilters"
                variant="ghost"
                color="neutral"
                size="sm"
                icon="i-heroicons-x-mark-20-solid"
                @click="clearAllSelections"
            >
                Clear All
            </UButton>
        </div>
    </div>
</template>
