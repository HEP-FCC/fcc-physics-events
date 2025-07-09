// A shared channel name and message to ensure tabs are on the same page.
const AUTH_CHANNEL_NAME = "fcc-physics-auth-channel";
const AUTH_SUCCESS_MESSAGE = "authentication-successful";

/**
 * Composable for managing user authentication state with an OAuth2 proxy.
 */
export const useAuth = () => {
    /**
     * Opens the CERN login page in a new tab.
     */
    const loginInNewTab = () => {
        const config = useRuntimeConfig();
        const redirectUrl = `${window.location.origin}/auth/callback`;
        const startUrl = `${config.public.apiBaseUrl}/authorized/oauth2/start?rd=${encodeURIComponent(redirectUrl)}`;

        window.open(startUrl, "_blank")?.focus();
    };

    /**
     * Listens for the success message from the login tab using a BroadcastChannel.
     * @param onAuthSuccess - The function to run when login is confirmed.
     * @returns A cleanup function to stop listening.
     */
    const listenForAuthSuccess = (onAuthSuccess: () => void) => {
        const authChannel = new BroadcastChannel(AUTH_CHANNEL_NAME);

        const handleMessage = (event: MessageEvent) => {
            if (event.data === AUTH_SUCCESS_MESSAGE) {
                onAuthSuccess();
                // Clean up the channel once its job is done.
                authChannel.close();
            }
        };

        authChannel.onmessage = handleMessage;

        // Return the cleanup function.
        return () => {
            authChannel.close();
        };
    };

    /**
     * Logs the user out.
     */
    const logout = () => {
        const config = useRuntimeConfig();
        window.location.href = `${config.public.apiBaseUrl}/oauth2/sign_out`;
    };

    return {
        loginInNewTab,
        listenForAuthSuccess,
        logout,
    };
};
