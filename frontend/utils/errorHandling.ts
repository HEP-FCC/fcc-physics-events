/**
 * Error handling utilities for API responses and user-friendly error messages
 */

export interface ApiError {
    message: string;
    status: number;
    details?:
        | {
              error?: string;
              message?: string;
          }
        | any;
}

export interface ErrorToastOptions {
    title: string;
    description: string;
    color: "error" | "warning";
}

/**
 * Parse API error and return user-friendly toast options
 */
export function parseApiError(error: unknown): ErrorToastOptions {
    console.log("Parsing API error:", error); // Debug log

    const apiError = error as ApiError;
    const status = apiError.status || (apiError as any).statusCode || 500;
    const errorType = apiError.details?.error;
    const errorMessage = apiError.details?.message || apiError.message;

    // Handle authentication and authorization errors (401)
    if (status === 401) {
        switch (errorType) {
            case "token_expired":
                return {
                    title: "Session Expired",
                    description:
                        "Your login session has expired. Please clear cookies and log in again to refresh your token.",
                    color: "warning",
                };

            case "missing_token":
            case "invalid_token":
            case "session_error":
                return {
                    title: "Authentication Required",
                    description:
                        "You need to log in to access this feature. If you were previously logged in, try clearing cookies and logging in again to refresh your token.",
                    color: "warning",
                };

            default:
                return {
                    title: "Unauthorized",
                    description:
                        "Authentication failed. Please try clearing your cookies and logging in again to refresh your token. If this does not help, contact website admins for help.",
                    color: "warning",
                };
        }
    }

    // Handle permission errors (403)
    if (status === 403) {
        return {
            title: "Permission Denied",
            description:
                "You don't have the required permissions for this action. Please contact the site administrators to request access.",
            color: "error",
        };
    }

    // Handle not found errors (404)
    if (status === 404) {
        return {
            title: "Not Found",
            description: "The requested resource was not found. It may have been deleted or moved.",
            color: "error",
        };
    }

    // Handle server errors (500+)
    if (status >= 500) {
        return {
            title: "Server Error",
            description: `A server error occurred. Please try again later or contact administrators if the problem persists. For more details, check the browser console (F12).`,
            color: "error",
        };
    }

    // Handle validation errors (400)
    if (status === 400) {
        return {
            title: "Invalid Request",
            description: errorMessage || "The request contains invalid data. Please check your input and try again.",
            color: "error",
        };
    }

    // Handle other client errors (4xx)
    if (status >= 400 && status < 500) {
        return {
            title: "Request Error",
            description: errorMessage || "There was a problem with your request. Please try again.",
            color: "error",
        };
    }

    // Generic error fallback
    const browserShortcut = navigator.platform.toLowerCase().includes("mac") ? "⌘+⌥+I" : "F12";

    return {
        title: "Unknown Error",
        description: `An unexpected error occurred: ${errorMessage || "Unknown error"}.

For troubleshooting:
• Check browser console (${browserShortcut}) for details
• Clear cookies and try again
• Contact site administrators if the problem persists`,
        color: "error",
    };
}

/**
 * Get browser shortcut for developer tools based on platform
 */
export function getDevToolsShortcut(): string {
    return navigator.platform.toLowerCase().includes("mac") ? "⌘+⌥+I" : "F12";
}
