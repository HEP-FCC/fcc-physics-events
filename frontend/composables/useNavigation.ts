import { ref, computed } from "vue";
import type { DropdownItem, DropdownType } from "~/types/dataset";

/**
 * Simple navigation state management with explicit reactivity
 */
export function useNavigation() {
    const { apiClient } = useApiClient();

    // Use individual refs for each dropdown to ensure reactivity
    const stageItems = ref<DropdownItem[]>([]);
    const campaignItems = ref<DropdownItem[]>([]);
    const detectorItems = ref<DropdownItem[]>([]);

    const stageLoading = ref(false);
    const campaignLoading = ref(false);
    const detectorLoading = ref(false);

    const stageOpen = ref(false);
    const campaignOpen = ref(false);
    const detectorOpen = ref(false);

    // Navigation configuration
    const navigationConfig = {
        stage: {
            icon: "i-heroicons-cpu-chip",
            label: "Stage",
            clearLabel: "Clear Stage",
        },
        campaign: {
            icon: "i-heroicons-calendar-days",
            label: "Campaign",
            clearLabel: "Clear Campaign",
        },
        detector: {
            icon: "i-heroicons-beaker",
            label: "Detector",
            clearLabel: "Clear Detector",
        },
    } as const;

    // Computed dropdowns object
    const dropdowns = computed(() => ({
        stage: {
            items: stageItems.value,
            isLoading: stageLoading.value,
            isOpen: stageOpen.value,
            ...navigationConfig.stage,
        },
        campaign: {
            items: campaignItems.value,
            isLoading: campaignLoading.value,
            isOpen: campaignOpen.value,
            ...navigationConfig.campaign,
        },
        detector: {
            items: detectorItems.value,
            isLoading: detectorLoading.value,
            isOpen: detectorOpen.value,
            ...navigationConfig.detector,
        },
    }));

    function getItemsRef(type: DropdownType) {
        switch (type) {
            case "stage":
                return stageItems;
            case "campaign":
                return campaignItems;
            case "detector":
                return detectorItems;
        }
    }

    function getLoadingRef(type: DropdownType) {
        switch (type) {
            case "stage":
                return stageLoading;
            case "campaign":
                return campaignLoading;
            case "detector":
                return detectorLoading;
        }
    }

    function getOpenRef(type: DropdownType) {
        switch (type) {
            case "stage":
                return stageOpen;
            case "campaign":
                return campaignOpen;
            case "detector":
                return detectorOpen;
        }
    }

    async function loadDropdownData(type: DropdownType, filters: Record<string, string> = {}, forceReload = false) {
        const itemsRef = getItemsRef(type);
        const loadingRef = getLoadingRef(type);

        // Skip if already loaded and not forcing reload, or if currently loading
        if ((itemsRef.value.length > 0 && !forceReload) || loadingRef.value) {
            return;
        }

        loadingRef.value = true;

        try {
            const newItems = await apiClient.getNavigationOptions(type, filters);

            itemsRef.value = newItems;
        } catch (error) {
            console.error(`Error loading ${type}:`, error);
            itemsRef.value = [];
        } finally {
            loadingRef.value = false;
        }
    }

    function toggleDropdown(type: DropdownType) {
        const openRef = getOpenRef(type);
        const wasOpen = openRef.value;

        // Close all dropdowns
        stageOpen.value = false;
        campaignOpen.value = false;
        detectorOpen.value = false;

        // Open the clicked one if it wasn't already open
        if (!wasOpen) {
            openRef.value = true;
        }
    }

    function closeAllDropdowns() {
        stageOpen.value = false;
        campaignOpen.value = false;
        detectorOpen.value = false;
    }

    function clearDropdownData(type: DropdownType) {
        const itemsRef = getItemsRef(type);
        itemsRef.value = [];
    }

    function clearDependentDropdowns(changedType: DropdownType) {
        if (changedType === "stage") {
            // Clear campaign and detector data
            campaignItems.value = [];
            detectorItems.value = [];
        } else if (changedType === "campaign") {
            // Clear detector data
            detectorItems.value = [];
        }
    }

    return {
        dropdowns,
        stageItems,
        campaignItems,
        detectorItems,
        stageLoading,
        campaignLoading,
        detectorLoading,
        stageOpen,
        campaignOpen,
        detectorOpen,
        loadDropdownData,
        toggleDropdown,
        closeAllDropdowns,
        clearDropdownData,
        clearDependentDropdowns,
    };
}
