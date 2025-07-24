// Auto-imported: ref, computed, readonly, watchEffect, type Ref
import type { DropdownItem } from "~/types/schema";
// Auto-imported: useNavigationConfig, getPreloadedDropdownData

/**
 * Dynamic navigation state management with schema-driven configuration
 */
export function useNavigationState() {
    const { baseUrl } = useTypedApiClient();
    const { getNavigationOrder, getNavigationItem, initializeNavigation, isNavigationReady } = useNavigationConfig();

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
    initializeNavigation().then(() => {
        initializeRefs();
        proactivelyLoadDropdownData();
    });

    // Also watch for changes in navigation order and update refs accordingly
    watchEffect(() => {
        const order = navigationOrder.value;
        if (order.length > 0) {
            initializeRefs();
            // Load dropdown data when navigation becomes ready
            if (isNavigationReady()) {
                proactivelyLoadDropdownData();
            }
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

    /**
     * Proactively load dropdown data in the background for better UX
     * Loads the appropriate dropdown level based on current navigation context
     */
    async function proactivelyLoadDropdownData(currentPath: Record<string, string | null> = {}) {
        if (!isNavigationReady() || navigationOrder.value.length === 0) {
            return;
        }

        const order = navigationOrder.value;

        try {
            // Determine which level to preload based on current navigation state
            let levelToPreload = 0; // Default to first level

            // Find the deepest level that has a value, then preload the next level
            for (let i = 0; i < order.length; i++) {
                const type = order[i];
                if (currentPath[type]) {
                    levelToPreload = i + 1; // Preload the next level after this one
                } else {
                    break; // Stop at the first empty level
                }
            }

            // Don't preload beyond the available levels
            if (levelToPreload >= order.length) {
                return;
            }

            const typeToPreload = order[levelToPreload];
            const itemsRef = getItemsRef(typeToPreload);
            const loadingRef = getLoadingRef(typeToPreload);

            // Only load if not already loaded or loading
            if (itemsRef && loadingRef && itemsRef.value.length === 0 && !loadingRef.value) {
                try {
                    // Check for preloaded data first (only for first level without filters)
                    if (levelToPreload === 0) {
                        const preloadedData = getPreloadedDropdownData(typeToPreload);
                        if (preloadedData && preloadedData.length > 0) {
                            itemsRef.value = preloadedData as DropdownItem[];
                            return;
                        }
                    }

                    // Build filters for the dropdown based on current path
                    const filters: Record<string, string> = {};
                    for (let i = 0; i < levelToPreload; i++) {
                        const filterType = order[i];
                        const filterValue = currentPath[filterType];
                        if (filterValue) {
                            filters[filterType] = filterValue;
                        }
                    }

                    // Fetch from API with appropriate filters
                    loadingRef.value = true;

                    let requestUrl = `/api/dropdown/${typeToPreload}`;
                    if (Object.keys(filters).length > 0) {
                        const params = new URLSearchParams();
                        const filterObj: Record<string, string> = {};
                        Object.entries(filters).forEach(([key, value]) => {
                            if (value?.trim()) {
                                const filterKey = key.endsWith("_name") ? key : `${key}_name`;
                                filterObj[filterKey] = value;
                            }
                        });

                        if (Object.keys(filterObj).length > 0) {
                            params.append("filters", JSON.stringify(filterObj));
                            requestUrl += `?${params.toString()}`;
                        }
                    }

                    const response = await fetch(`${baseUrl}${requestUrl}`);

                    if (response.ok) {
                        const data = await response.json();
                        const items = data.data || [];
                        itemsRef.value = items;
                    } else {
                        console.warn(`Failed to load ${typeToPreload}: ${response.status}`);
                    }
                } catch (error) {
                    console.warn(`Error loading ${typeToPreload}:`, error);
                } finally {
                    if (loadingRef) {
                        loadingRef.value = false;
                    }
                }
            }
        } catch (error) {
            console.warn("Error during proactive dropdown loading:", error);
        }
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

        // Check for preloaded data first (only if no filters and no force reload)
        const hasFilters = Object.keys(filters).length > 0;
        if (!forceReload && !hasFilters) {
            // First check if we have preloaded data available
            const preloadedData = getPreloadedDropdownData(type);
            if (preloadedData && preloadedData.length > 0) {
                itemsRef.value = preloadedData as DropdownItem[];
                return; // Exit early, no need to make API call
            }

            // If no preloaded data but items already loaded, skip API call
            if (itemsRef.value.length > 0) {
                return;
            }
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

            const response = await fetch(`${baseUrl}${requestUrl}`);
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
        proactivelyLoadDropdownData,
    };
}
