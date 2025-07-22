import { watch } from "vue";
import { APP_CONFIG } from "~/config/app.config";

interface User {
    given_name?: string;
    family_name?: string;
    preferred_username?: string;
    // [key: string]: any;
}

interface AuthState {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;
}

/**
 * Authentication composable for CERN OAuth with cookie-based sessions
 * Handles login, logout, and user session management
 */
export function useAuth() {
    const { apiClient } = useApiClient();

    // Use global state to ensure consistency across components
    const authState = useState<AuthState>(
        "auth-state",
        (): AuthState => ({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
        }),
    );

    // Watch the cookie for changes and update auth state automatically
    const authCookie = useCookie(APP_CONFIG.auth.cookieName);

    watch(
        authCookie,
        (newCookieValue) => {
            if (newCookieValue) {
                const cookieData = newCookieValue as unknown as Record<string, unknown>;
                if (cookieData.token && cookieData.user) {
                    authState.value.isAuthenticated = true;
                    authState.value.user = cookieData.user;
                    authState.value.error = null;
                } else {
                    authState.value.isAuthenticated = false;
                    authState.value.user = null;
                }
            } else {
                authState.value.isAuthenticated = false;
                authState.value.user = null;
            }
        },
        { immediate: true },
    );

    /**
     * Check if user is currently authenticated by checking the frontend cookie
     */
    async function checkAuthStatus(): Promise<void> {
        // The watcher handles most of the work, but we can trigger it manually if needed
        authState.value.isLoading = true;
        authState.value.error = null;

        try {
            const authCookie = useCookie(APP_CONFIG.auth.cookieName);
            // Trigger watcher by accessing the cookie value
            const _cookieValue = authCookie.value;

            // The watcher will update the auth state based on the cookie value
        } catch {
            authState.value.error = "Authentication check failed";
        } finally {
            authState.value.isLoading = false;
        }
    }

    /**
     * Initiate login flow - redirects to CERN OAuth
     */
    function login(): void {
        authState.value.error = null;
        apiClient.initiateLogin();
    }

    /**
     * Logout user and clear cookie
     */
    async function logout(): Promise<void> {
        authState.value.isLoading = true;
        authState.value.error = null;

        try {
            // Get logout URL from backend
            const logoutResponse = await apiClient.logout();

            // Clear the auth cookie
            const authCookie = useCookie(APP_CONFIG.auth.cookieName);
            authCookie.value = null;

            authState.value.isAuthenticated = false;
            authState.value.user = null;

            // Redirect to CERN SSO logout if URL provided
            if (logoutResponse?.logout_url) {
                window.location.href = logoutResponse.logout_url;
            }
        } catch {
            // Clear the auth cookie
            const authCookie = useCookie(APP_CONFIG.auth.cookieName);
            authCookie.value = null;
            authState.value.isAuthenticated = false;
            authState.value.user = null;
        } finally {
            authState.value.isLoading = false;
        }
    }

    /**
     * Handle OAuth callback - not needed with cookie auth,
     * but kept for compatibility
     */
    async function handleAuthCallback(): Promise<void> {
        // With cookie-based auth, this is handled by the backend
        // Just check auth status after callback
        await checkAuthStatus();
    }

    /**
     * Clear authentication error
     */
    function clearError(): void {
        authState.value.error = null;
    }

    /**
     * Get access token for API calls from cookie
     */
    async function getAccessToken(): Promise<string | null> {
        const authCookie = useCookie(APP_CONFIG.auth.cookieName);
        const cookieData = authCookie.value as unknown as Record<string, unknown>;

        if (cookieData?.token && typeof cookieData.token === "string") {
            return cookieData.token;
        }

        throw new Error("No access token available. Please login.");
    }

    /**
     * Refresh current session for browser-based authentication
     */
    async function refreshSession(): Promise<void> {
        // Just validate the current cookie
        await checkAuthStatus();
    }

    return {
        // Readonly state
        authState: readonly(authState),
        isAuthenticated: readonly(computed(() => authState.value.isAuthenticated)),
        user: readonly(computed(() => authState.value.user)),
        isLoading: readonly(computed(() => authState.value.isLoading)),
        error: readonly(computed(() => authState.value.error)),

        // Methods
        checkAuthStatus,
        login,
        logout,
        handleAuthCallback,
        getAccessToken,
        refreshSession,
        clearError,
    };
}
