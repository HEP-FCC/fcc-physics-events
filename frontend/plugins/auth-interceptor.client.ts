/**
 * Auth interceptor plugin for handling automatic token refresh
 * This plugin sets up global error handling and token refresh logic
 */

export default defineNuxtPlugin(() => {
    // This plugin runs on client-side only to handle auth interceptors
    
    // Optional: Add global error handler for unhandled auth errors
    const handleGlobalAuthError = (error: any) => {
        console.log('Global auth error handler:', error);
        
        // Check if this is an auth-related error that wasn't handled by the API client
        if (error?.status === 401 || error?.statusCode === 401) {
            // This would only trigger if the automatic refresh also failed
            console.warn('Authentication failed globally. User may need to re-login.');
        }
    };

    // Set up global error handler
    if (process.client) {
        window.addEventListener('unhandledrejection', (event) => {
            handleGlobalAuthError(event.reason);
        });
    }

    console.log('Auth interceptor plugin initialized');
});
