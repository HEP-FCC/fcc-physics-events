/**
 * Utility composable for managing loading states with delays to prevent flickering
 */
import { ref, onUnmounted } from "vue";

export interface LoadingDelayOptions {
    /** Delay in milliseconds before showing loading indicator (default: 300ms) */
    delayMs?: number;
}

/**
 * Creates a loading state that only becomes visible after a specified delay.
 * Prevents loading spinners from flashing on fast requests, improving UX.
 */
export function useLoadingDelay(options: LoadingDelayOptions = {}) {
    const { delayMs = 300 } = options;

    const isLoadingActive = ref(false);
    const shouldShowLoadingIndicator = ref(false);
    let delayTimeoutId: NodeJS.Timeout | null = null;

    function startLoading() {
        isLoadingActive.value = true;
        delayTimeoutId = setTimeout(() => {
            shouldShowLoadingIndicator.value = true;
        }, delayMs);
    }

    function stopLoading() {
        isLoadingActive.value = false;
        shouldShowLoadingIndicator.value = false;
        if (delayTimeoutId) {
            clearTimeout(delayTimeoutId);
            delayTimeoutId = null;
        }
    }

    // Cleanup timeout on component unmount
    onUnmounted(() => {
        if (delayTimeoutId) {
            clearTimeout(delayTimeoutId);
            delayTimeoutId = null;
        }
    });

    return {
        isLoading: isLoadingActive,
        shouldShowLoading: shouldShowLoadingIndicator,
        startLoading,
        stopLoading,
    };
}
