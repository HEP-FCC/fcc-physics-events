import { ref, computed, readonly, watchEffect, type Ref } from "vue";
import type { DropdownItem } from "~/types/schema";
import { useApiClient } from "~/composables/useApiClient";
import { useNavigationConfig } from "~/composables/useNavigationConfig";

/**
 * Dynamic navigation state management with schema-driven configuration
 */
export function useNavigationState() {
    const { apiClient } = useApiClient();
    const {
        getNavigationOrder,
        getNavigationItem,
        initializeNavigation,
        isNavigationReady,
        isLoading: isConfigLoading,
    } = useNavigationConfig();

    // Dynamic refs based on navigation order
    const navigationOrder = computed(() => getNavigationOrder());

    // Create dynamic refs for each navigation type
    const itemsRefs: Record<string, Ref<DropdownItem[]>> = {};
    const loadingRefs: Record<string, Ref<boolean>> = {};
    const openRefs: Record<string, Ref<boolean>> = {};

    // Initialize navigation and setup refs
    const initializeRefs = () => {
        const order = navigationOrder.value;
        order.forEach((type) => {
            if (!itemsRefs[type]) {
                itemsRefs[type] = ref<DropdownItem[]>([]);
                loadingRefs[type] = ref(false);
                openRefs[type] = ref(false);
            }
        });
    };

    // Initialize navigation configuration and refs
    const initPromise = initializeNavigation().then(() => {
        initializeRefs();
    });

    // Also watch for changes in navigation order and update refs accordingly
    watchEffect(() => {
        const order = navigationOrder.value;
        if (order.length > 0) {
            initializeRefs();
        }
    });

    // Computed dropdowns object
    const dropdowns = computed(() => {
        const result: Record<
            string,
            {
                items: DropdownItem[];
                isLoading: boolean;
                isOpen: boolean;
                icon: string;
                label: string;
                clearLabel: string;
            }
        > = {};

        // Only process navigation if config is ready and we have navigation order
        if (isNavigationReady() && navigationOrder.value.length > 0) {
            try {
                navigationOrder.value.forEach((type) => {
                    const config = getNavigationItem(type);
                    result[type] = {
                        items: itemsRefs[type]?.value || [],
                        isLoading: loadingRefs[type]?.value || false,
                        isOpen: openRefs[type]?.value || false,
                        icon: config.icon,
                        label: config.label,
                        clearLabel: `Clear ${config.label}`,
                    };
                });
            } catch (error) {
                console.error("Error building dropdowns configuration:", error);
                // Return empty object if there's an error
                return {};
            }
        }

        return result;
    });

    function getItemsRef(type: string): Ref<DropdownItem[]> | null {
        const result = itemsRefs[type] || null;
        return result;
    }

    function getLoadingRef(type: string): Ref<boolean> | null {
        const result = loadingRefs[type] || null;
        return result;
    }

    function getOpenRef(type: string): Ref<boolean> | null {
        return openRefs[type] || null;
    }

    async function loadDropdownData(type: string, filters: Record<string, string> = {}, forceReload: boolean = false) {
        // Ensure navigation is initialized first
        await initializeNavigation();

        const itemsRef = getItemsRef(type);
        const loadingRef = getLoadingRef(type);

        if (!itemsRef || !loadingRef) {
            console.warn(`Unknown navigation type: ${type}`, { itemsRef, loadingRef });
            return;
        }

        // Skip if already loading
        if (loadingRef.value) {
            return;
        }

        // Skip if data already loaded and no filters (unless force reload)
        const hasFilters = Object.keys(filters).length > 0;
        if (!forceReload && !hasFilters && itemsRef.value.length > 0) {
            return;
        }

        loadingRef.value = true;

        try {
            // Use the new generic API endpoint directly
            let requestUrl = `/api/dropdown/${type}`;

            if (Object.keys(filters).length > 0) {
                const params = new URLSearchParams();
                // Convert filters to the format expected by the new endpoint
                const filterObj: Record<string, string> = {};
                Object.entries(filters).forEach(([key, value]) => {
                    if (value?.trim()) {
                        // Convert from type to type_name for the backend filter
                        const filterKey = key.endsWith("_name") ? key : `${key}_name`;
                        filterObj[filterKey] = value;
                    }
                });

                if (Object.keys(filterObj).length > 0) {
                    params.append("filters", JSON.stringify(filterObj));
                    requestUrl += `?${params.toString()}`;
                }
            }

            const response = await fetch(`${apiClient.baseUrl}${requestUrl}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            itemsRef.value = data.data || [];
        } catch (error) {
            console.error(`Error loading ${type}:`, error);
            itemsRef.value = [];
        } finally {
            loadingRef.value = false;
        }
    }

    function toggleDropdown(type: string) {
        const openRef = getOpenRef(type);
        if (!openRef) {
            return;
        }

        const wasOpen = openRef.value;

        // Close all dropdowns
        closeAllDropdowns();

        // Open the clicked one if it wasn't already open
        if (!wasOpen) {
            openRef.value = true;
        }
    }

    function closeAllDropdowns() {
        const order = navigationOrder.value;
        order.forEach((type: string) => {
            const openRef = getOpenRef(type);
            if (openRef) {
                openRef.value = false;
            }
        });
    }

    function clearDropdownData(type: string) {
        const itemsRef = getItemsRef(type);
        if (itemsRef) {
            itemsRef.value = [];
        }
    }

    function clearDependentDropdowns(changedType: string) {
        const order = navigationOrder.value;
        const typeIndex = order.indexOf(changedType);
        if (typeIndex === -1) return;

        // Clear all subsequent navigation types
        for (let i = typeIndex + 1; i < order.length; i++) {
            const dependentType = order[i];
            const itemsRef = getItemsRef(dependentType);
            if (itemsRef) {
                itemsRef.value = [];
            }
        }
    }

    // Utility functions for compatibility
    function getItems(type: string): DropdownItem[] {
        const itemsRef = getItemsRef(type);
        return itemsRef ? itemsRef.value : [];
    }

    function isLoading(type: string): boolean {
        const loadingRef = getLoadingRef(type);
        return loadingRef ? loadingRef.value : false;
    }

    function isOpen(type: string): boolean {
        const openRef = getOpenRef(type);
        return openRef ? openRef.value : false;
    }

    return {
        dropdowns,
        itemsRefs: readonly(itemsRefs),
        loadingRefs: readonly(loadingRefs),
        openRefs: readonly(openRefs),
        loadDropdownData,
        toggleDropdown,
        closeAllDropdowns,
        clearDropdownData,
        clearDependentDropdowns,
        getItems,
        isLoading,
        isOpen,
        navigationOrder,
    };
}
