import { ref, readonly } from "vue";

interface User {
    email?: string;
    name?: string;
    preferred_username?: string;
    sub?: string;
    [key: string]: any;
}

interface AuthState {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;
    accessToken: string | null;
}

/**
 * Authentication composable for CERN OAuth
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
            accessToken: null,
        }),
    );

    /**
     * Check if user is currently authenticated
     */
    async function checkAuthStatus(): Promise<void> {
        authState.value.isLoading = true;
        authState.value.error = null;

        try {
            // Check if we have a stored token
            const token = localStorage.getItem("auth_token");
            if (!token) {
                authState.value.isAuthenticated = false;
                authState.value.user = null;
                authState.value.accessToken = null;
                return;
            }

            // Validate token with backend
            const response = await apiClient.getCurrentUser(token);
            authState.value.isAuthenticated = response.authenticated;
            authState.value.user = response.user || null;
            authState.value.accessToken = token;
        } catch (error) {
            // Token invalid, clear it
            localStorage.removeItem("auth_token");
            authState.value.isAuthenticated = false;
            authState.value.user = null;
            authState.value.accessToken = null;
            authState.value.error = "Authentication expired";
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
     * Logout user and clear token
     */
    async function logout(): Promise<void> {
        authState.value.isLoading = true;
        authState.value.error = null;

        try {
            // Clear stored token
            localStorage.removeItem("auth_token");
            authState.value.isAuthenticated = false;
            authState.value.user = null;
            authState.value.accessToken = null;

            // Optionally notify backend (not strictly necessary for JWT)
            await apiClient.logout();
        } catch (error) {
            // Still clear local state even if server call fails
            authState.value.isAuthenticated = false;
            authState.value.user = null;
            authState.value.accessToken = null;
        } finally {
            authState.value.isLoading = false;
        }
    }

    /**
     * Handle OAuth callback with token from URL fragment
     */
    async function handleAuthCallback(token?: string): Promise<void> {
        authState.value.isLoading = true;
        authState.value.error = null;

        try {
            if (!token) {
                throw new Error("No token provided");
            }

            // Store token securely
            localStorage.setItem("auth_token", token);
            authState.value.accessToken = token;

            // Validate token and get user info
            await checkAuthStatus();
        } catch (error) {
            authState.value.error = "Authentication failed";
            authState.value.isAuthenticated = false;
            authState.value.user = null;
            authState.value.accessToken = null;
            localStorage.removeItem("auth_token");
        } finally {
            authState.value.isLoading = false;
        }
    }

    /**
     * Clear authentication error
     */
    function clearError(): void {
        authState.value.error = null;
    }

    /**
     * Get access token for API calls
     */
    async function getAccessToken(): Promise<string | null> {
        // Return stored token if available
        if (authState.value.accessToken) {
            return authState.value.accessToken;
        }

        // Check localStorage for token
        const token = localStorage.getItem("auth_token");
        if (token) {
            authState.value.accessToken = token;
            return token;
        }

        throw new Error("No access token available. Please login.");
    }

    /**
     * Refresh current session for browser-based authentication
     */
    async function refreshSession(): Promise<void> {
        // For JWT tokens, we don't need server-side session refresh
        // Just validate the current token
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
