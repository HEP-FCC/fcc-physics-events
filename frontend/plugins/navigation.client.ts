/**
 * Navigation Initialization Plugin
 *
 * This plugin initializes navigation configuration early in the application lifecycle
 * to ensure badge colors are available immediately when entities are displayed.
 */
export default defineNuxtPlugin(async () => {
    if (process.client) {
        // Only run on client-side to avoid SSR issues
        const { initializeNavigation } = useDynamicNavigation();

        try {
            // Start navigation initialization immediately
            // This runs in parallel with other app initialization
            await initializeNavigation();
        } catch (error) {
            console.warn("Failed to initialize navigation in plugin:", error);
        }
    }
});
