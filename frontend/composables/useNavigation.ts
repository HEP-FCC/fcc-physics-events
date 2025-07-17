import { ref, computed } from "vue";
import type { DropdownItem, DropdownType } from "~/types/dataset";
import { DROPDOWN_ORDER, NAVIGATION_CONFIG } from "~/config/navigation";

/**
 * Simple navigation state management with explicit reactivity
 */
export function useNavigation() {
    const { apiClient } = useApiClient();

    // Use individual refs for each dropdown to ensure reactivity
    const stageItems = ref<DropdownItem[]>([]);
    const acceleratorItems = ref<DropdownItem[]>([]);
    const campaignItems = ref<DropdownItem[]>([]);
    const detectorItems = ref<DropdownItem[]>([]);

    const stageLoading = ref(false);
    const acceleratorLoading = ref(false);
    const campaignLoading = ref(false);
    const detectorLoading = ref(false);

    const stageOpen = ref(false);
    const acceleratorOpen = ref(false);
    const campaignOpen = ref(false);
    const detectorOpen = ref(false);

    // Navigation configuration - now imported from centralized config
    // NAVIGATION_CONFIG is already imported and contains all dropdown configurations

    // Computed dropdowns object
    const dropdowns = computed(() => ({
        stage: {
            items: stageItems.value,
            isLoading: stageLoading.value,
            isOpen: stageOpen.value,
            ...NAVIGATION_CONFIG.stage,
        },
        accelerator: {
            items: acceleratorItems.value,
            isLoading: acceleratorLoading.value,
            isOpen: acceleratorOpen.value,
            ...NAVIGATION_CONFIG.accelerator,
        },
        campaign: {
            items: campaignItems.value,
            isLoading: campaignLoading.value,
            isOpen: campaignOpen.value,
            ...NAVIGATION_CONFIG.campaign,
        },
        detector: {
            items: detectorItems.value,
            isLoading: detectorLoading.value,
            isOpen: detectorOpen.value,
            ...NAVIGATION_CONFIG.detector,
        },
    }));

    function getItemsRef(type: DropdownType) {
        switch (type) {
            case "stage":
                return stageItems;
            case "accelerator":
                return acceleratorItems;
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
            case "accelerator":
                return acceleratorLoading;
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
            case "accelerator":
                return acceleratorOpen;
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
        acceleratorOpen.value = false;
        campaignOpen.value = false;
        detectorOpen.value = false;

        // Open the clicked one if it wasn't already open
        if (!wasOpen) {
            openRef.value = true;
        }
    }

    function closeAllDropdowns() {
        stageOpen.value = false;
        acceleratorOpen.value = false;
        campaignOpen.value = false;
        detectorOpen.value = false;
    }

    function clearDropdownData(type: DropdownType) {
        const itemsRef = getItemsRef(type);
        itemsRef.value = [];
    }

    function clearDependentDropdowns(changedType: DropdownType) {
        const changedIndex = DROPDOWN_ORDER.indexOf(changedType);

        // Clear all dropdowns that come after the changed one in the hierarchy
        DROPDOWN_ORDER.slice(changedIndex + 1).forEach((type) => {
            const itemsRef = getItemsRef(type);
            itemsRef.value = [];
        });
    }

    return {
        dropdowns,
        stageItems,
        acceleratorItems,
        campaignItems,
        detectorItems,
        stageLoading,
        acceleratorLoading,
        campaignLoading,
        detectorLoading,
        stageOpen,
        acceleratorOpen,
        campaignOpen,
        detectorOpen,
        loadDropdownData,
        toggleDropdown,
        closeAllDropdowns,
        clearDropdownData,
        clearDependentDropdowns,
    };
}
