import { ref, computed, readonly, type Ref } from "vue";
import type { DropdownItem } from "~/types/schema";
import { APP_CONFIG } from "~/config/app.config";
import { useApiClient } from "~/composables/useApiClient";

/**
 * Dynamic navigation state management with schema-driven configuration
 */
export function useNavigationState() {
    const { apiClient } = useApiClient();

    // Dynamic refs based on navigation order
    const navigationOrder = APP_CONFIG.navigationOrder;

    // Create dynamic refs for each navigation type
    const itemsRefs: Record<string, Ref<DropdownItem[]>> = {};
    const loadingRefs: Record<string, Ref<boolean>> = {};
    const openRefs: Record<string, Ref<boolean>> = {};

    // Initialize refs for each navigation type
    navigationOrder.forEach((type) => {
        itemsRefs[type] = ref<DropdownItem[]>([]);
        loadingRefs[type] = ref(false);
        openRefs[type] = ref(false);
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

        navigationOrder.forEach((type) => {
            const config = APP_CONFIG.navigationOverrides[type as keyof typeof APP_CONFIG.navigationOverrides];
            result[type] = {
                items: itemsRefs[type]?.value || [],
                isLoading: loadingRefs[type]?.value || false,
                isOpen: openRefs[type]?.value || false,
                icon: config?.icon || "i-heroicons-folder",
                label: config?.label || type,
                clearLabel: `Clear ${config?.label || type}`,
            };
        });

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
            const newItems = await apiClient.getNavigationOptions(
                type as "stage" | "campaign" | "detector" | "accelerator",
                filters,
            );
            itemsRef.value = newItems;
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
        navigationOrder.forEach((type) => {
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
        const typeIndex = (navigationOrder as readonly string[]).indexOf(changedType);
        if (typeIndex === -1) return;

        // Clear all subsequent navigation types
        for (let i = typeIndex + 1; i < navigationOrder.length; i++) {
            const dependentType = navigationOrder[i];
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
