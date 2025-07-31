/**
 * Global Error Handler Plugin for Nuxt
 * Centralized error handling for all application errors with user-friendly notifications
 */

import type { ComponentPublicInstance } from "vue";

// Extended API Error interface for error handling (more flexible than types/api.ts)
interface UnifiedApiError {
    message: string;
    status: number;
    details?: {
        error?: string;
        message?: string;
        type?: string;
        code?: string;
        retry_after?: number;
        required_role?: string;
        validation_errors?: Record<string, string[]>;
    };
    statusCode?: number;
    data?: any;
    headers?: Record<string, string>;
}

// Error types that backend should use consistently
export const ERROR_TYPES = {
    // Authentication (401)
    TOKEN_EXPIRED: "token_expired",
    TOKEN_INVALID: "invalid_token",
    TOKEN_MISSING: "missing_token",
    SESSION_ERROR: "session_error",

    // Authorization (403)
    INSUFFICIENT_PERMISSIONS: "insufficient_permissions",
    ROLE_REQUIRED: "role_required",

    // Validation (400)
    INVALID_INPUT: "invalid_input",
    MISSING_FIELD: "missing_field",
    INVALID_FORMAT: "invalid_format",

    // Rate Limiting (429)
    RATE_LIMITED: "rate_limited",

    // Server Errors (500+)
    INTERNAL_ERROR: "internal_error",
    DATABASE_ERROR: "database_error",
    EXTERNAL_SERVICE_ERROR: "external_service_error",
} as const;

export type ErrorType = (typeof ERROR_TYPES)[keyof typeof ERROR_TYPES];

interface ErrorContext {
    component?: string;
    lifecycle?: string;
    route?: string;
    timestamp?: Date;
    userAgent?: string;
    sessionId?: string;
    userId?: string;
    buildId?: string;
    promise?: Promise<any>;
    errorId?: string;
    requestId?: string;
    retryCount?: number;
    [key: string]: any;
}

interface ErrorHandlerOptions {
    enableConsoleLogging?: boolean;
    enableToastNotifications?: boolean;
    enableErrorReporting?: boolean;
    maxRetries?: number;
    retryDelay?: number;
    retryableStatuses?: number[];
    excludeFromRetry?: string[];
}

interface ErrorToastOptions {
    title: string;
    description: string;
    color: "error" | "warning" | "info";
}

// Global state for error tracking and retry management
const errorState = reactive({
    retryCounters: new Map<string, number>(),
    rateLimitResets: new Map<string, number>(),
    isMaintenanceMode: false,
    lastNetworkError: null as Date | null,
});

/**
 * Parse API error and return user-friendly toast options
 */
function parseApiError(error: unknown): ErrorToastOptions {
    console.log("Parsing API error:", error);

    const apiError = error as UnifiedApiError;
    const status = apiError.status || (apiError as any).statusCode || 500;
    const errorType = apiError.details?.error;
    const errorMessage = apiError.details?.message || apiError.message;

    // Handle authentication errors (401)
    if (status === 401) {
        switch (errorType) {
            case ERROR_TYPES.TOKEN_EXPIRED:
                return {
                    title: "Session Expired",
                    description:
                        "Your login session has expired. Please clear cookies and log in again to refresh your token.",
                    color: "warning",
                };
            case ERROR_TYPES.TOKEN_MISSING:
            case ERROR_TYPES.TOKEN_INVALID:
            case ERROR_TYPES.SESSION_ERROR:
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

    // Handle authorization errors (403)
    if (status === 403) {
        if (errorType === ERROR_TYPES.ROLE_REQUIRED) {
            const requiredRole = apiError.details?.required_role;
            return {
                title: "Permission Denied",
                description: `You need ${
                    requiredRole || "additional permissions"
                } to perform this action. Please contact the site administrators to request access.`,
                color: "error",
            };
        }
        return {
            title: "Permission Denied",
            description:
                "You don't have the required permissions for this action. Please contact the site administrators to request access.",
            color: "error",
        };
    }

    // Handle validation errors (400)
    if (status === 400) {
        if (errorType === ERROR_TYPES.INVALID_INPUT && apiError.details?.validation_errors) {
            const validationErrors = apiError.details.validation_errors;
            const fieldErrors = Object.entries(validationErrors)
                .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(", ") : String(errors)}`)
                .join("; ");
            return {
                title: "Validation Error",
                description: `Please fix the following errors: ${fieldErrors}`,
                color: "error",
            };
        }
        return {
            title: "Invalid Request",
            description: errorMessage || "The request contains invalid data. Please check your input and try again.",
            color: "error",
        };
    }

    // Handle rate limiting (429)
    if (status === 429) {
        const retryAfter = apiError.details?.retry_after;
        const retryTime = typeof retryAfter === "number" ? retryAfter : 60;
        return {
            title: "Rate Limited",
            description: `Too many requests. Please wait ${retryTime} seconds before trying again.`,
            color: "warning",
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
        const browserShortcut = navigator.platform.toLowerCase().includes("mac") ? "⌘+⌥+I" : "F12";

        switch (errorType) {
            case ERROR_TYPES.DATABASE_ERROR:
                return {
                    title: "Database Error",
                    description:
                        "A database error occurred. Please try again later or contact administrators if the problem persists.",
                    color: "error",
                };
            case ERROR_TYPES.EXTERNAL_SERVICE_ERROR:
                return {
                    title: "Service Unavailable",
                    description: "An external service is temporarily unavailable. Please try again in a few minutes.",
                    color: "error",
                };
            default:
                return {
                    title: "Server Error",
                    description: `A server error occurred. Please try again later or contact administrators if the problem persists. For more details, check the browser console (${browserShortcut}).`,
                    color: "error",
                };
        }
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

// Helper functions
function isApiError(error: unknown): error is UnifiedApiError {
    return (
        typeof error === "object" &&
        error !== null &&
        ("status" in error || "statusCode" in error) &&
        "message" in error
    );
}

function isNetworkError(error: unknown): boolean {
    return (
        error instanceof TypeError ||
        (error as any)?.name === "NetworkError" ||
        (error as any)?.code === "NETWORK_ERROR" ||
        navigator.onLine === false
    );
}

export default defineNuxtPlugin({
    name: "global-error-handler",
    setup(nuxtApp) {
        const toast = useToast();
        const { login, logout } = useAuth();

        const options: ErrorHandlerOptions = {
            enableConsoleLogging: true,
            enableToastNotifications: true,
            enableErrorReporting: process.env.NODE_ENV === "production",
            maxRetries: 3,
            retryDelay: 1000,
            retryableStatuses: [408, 429, 500, 502, 503, 504],
            excludeFromRetry: ["/auth/", "/login", "/logout"],
        };

        // Enhanced Vue error handler with component context
        nuxtApp.vueApp.config.errorHandler = (err: unknown, instance: ComponentPublicInstance | null, info: string) => {
            const error = err instanceof Error ? err : new Error(String(err));
            const context: ErrorContext = {
                component: instance?.$options.name || instance?.$options.__name || "Unknown",
                lifecycle: info,
                route: useRoute().fullPath,
                timestamp: new Date(),
                userAgent: navigator.userAgent,
            };

            console.error("[Vue Error]", { error, context });
            handleError(error, "Vue Component Error", context);
        };

        // Network status monitoring
        window.addEventListener("online", () => {
            if (errorState.lastNetworkError) {
                toast.add({
                    title: "Connection Restored",
                    description: "Your internet connection is back. Retrying failed requests...",
                    color: "success",
                    duration: 3000,
                });
                errorState.lastNetworkError = null;
            }
        });

        window.addEventListener("offline", () => {
            errorState.lastNetworkError = new Date();
            toast.add({
                title: "Connection Lost",
                description: "Check your internet connection. We'll retry when it's restored.",
                color: "warning",
                progress: false,
            });
        });

        // Global unhandled promise rejection handler
        window.addEventListener("unhandledrejection", (event) => {
            const context: ErrorContext = {
                component: "Global",
                lifecycle: "Promise Rejection",
                route: useRoute().fullPath,
                timestamp: new Date(),
                userAgent: navigator.userAgent,
                promise: event.promise,
            };

            console.error("[Unhandled Promise Rejection]", { reason: event.reason, context });
            event.preventDefault();
            handleError(event.reason, "Unhandled Promise Rejection", context);
        });

        // Core error handling function
        function handleError(error: unknown, contextName: string, context?: ErrorContext): boolean {
            if (options.enableConsoleLogging) {
                console.error(`[Error Handler - ${contextName}]`, { error, context });
            }

            // Skip API errors from useApiClient for non-component errors - they're already handled there
            if (
                isApiError(error) &&
                contextName !== "Vue Component Error" &&
                contextName !== "Unhandled Promise Rejection"
            ) {
                return false; // Let useApiClient handle it
            }

            // Check for network errors
            if (isNetworkError(error)) {
                return handleNetworkError(error, context);
            }

            // Check if it's an API error from Vue components or unhandled promises
            if (isApiError(error)) {
                return handleApiError(error, contextName, context);
            }

            // Handle generic JavaScript errors
            return handleGenericError(error, contextName, context);
        }

        function handleApiError(error: UnifiedApiError, contextName: string, context?: ErrorContext): boolean {
            const requestKey = context?.route || "unknown";

            // Handle authentication errors (401)
            if (error.status === 401) {
                return handleAuthError(error, context);
            }

            // Handle authorization errors (403)
            if (error.status === 403) {
                return handleAuthorizationError(error, context);
            }

            // Handle rate limiting (429)
            if (error.status === 429) {
                return handleRateLimitError(error, context);
            }

            // Handle retryable server errors
            if (options.retryableStatuses?.includes(error.status)) {
                const shouldRetry = checkRetryEligibility(requestKey, context);
                if (shouldRetry) {
                    return scheduleRetry(error, requestKey, context);
                }
            }

            // Show user-friendly error message
            if (options.enableToastNotifications) {
                const toastOptions = parseApiError(error);
                toast.add({
                    ...toastOptions,
                    duration: 10000,
                });
            }

            return true;
        }

        function handleAuthError(error: UnifiedApiError, context?: ErrorContext): boolean {
            // Clear any existing retry counters for auth errors
            errorState.retryCounters.clear();

            const toastOptions = parseApiError(error);

            if (options.enableToastNotifications) {
                const toastOptions = parseApiError(error);
                toast.add({
                    ...toastOptions,
                    actions: [
                        {
                            label: "Login",
                            onClick: () => login(),
                        },
                    ],
                });
            }

            return true;
        }

        function handleAuthorizationError(error: UnifiedApiError, context?: ErrorContext): boolean {
            if (options.enableToastNotifications) {
                const toastOptions = parseApiError(error);
                toast.add({
                    ...toastOptions,
                });
            }

            return true;
        }

        function handleRateLimitError(error: UnifiedApiError, context?: ErrorContext): boolean {
            const retryAfter = error.details?.retry_after;
            const retryTime = typeof retryAfter === "number" ? retryAfter : 60;
            const requestKey = context?.route || "unknown";

            // Store rate limit reset time
            errorState.rateLimitResets.set(requestKey, Date.now() + retryTime * 1000);

            if (options.enableToastNotifications) {
                const toastOptions = parseApiError(error);
                toast.add(toastOptions);
            }

            return true;
        }

        function handleNetworkError(error: unknown, context?: ErrorContext): boolean {
            errorState.lastNetworkError = new Date();

            if (options.enableToastNotifications) {
                toast.add({
                    title: "Connection Problem",
                    description:
                        "Unable to connect to the server. Please check your internet connection and try again.",
                    color: "warning",
                });
            }

            return true;
        }

        function handleGenericError(error: unknown, contextName: string, context?: ErrorContext): boolean {
            const errorMessage = error instanceof Error ? error.message : String(error);

            if (options.enableToastNotifications) {
                toast.add({
                    title: "Application Error",
                    description: `An unexpected error occurred: ${errorMessage}`,
                    color: "error",
                });
            }

            return true;
        }

        function checkRetryEligibility(requestKey: string, context?: ErrorContext): boolean {
            const currentRetries = errorState.retryCounters.get(requestKey) || 0;
            const maxRetries = options.maxRetries || 3;

            // Check if route is excluded from retry
            if (options.excludeFromRetry?.some((pattern) => context?.route?.includes(pattern))) {
                return false;
            }

            // Check if we're still within rate limit
            const rateLimitReset = errorState.rateLimitResets.get(requestKey);
            if (rateLimitReset && Date.now() < rateLimitReset) {
                return false;
            }

            return currentRetries < maxRetries;
        }

        function scheduleRetry(error: UnifiedApiError, requestKey: string, context?: ErrorContext): boolean {
            const currentRetries = errorState.retryCounters.get(requestKey) || 0;
            const newRetryCount = currentRetries + 1;

            errorState.retryCounters.set(requestKey, newRetryCount);

            const delay = (options.retryDelay || 1000) * Math.pow(2, currentRetries); // Exponential backoff

            if (options.enableToastNotifications) {
                toast.add({
                    title: "Retrying Request",
                    description: `Attempt ${newRetryCount} of ${options.maxRetries}. Retrying in ${
                        delay / 1000
                    } seconds...`,
                    color: "info",
                });
            }

            // Note: Actual retry logic would need to be implemented by the calling code
            // This just tracks the retry state and shows user feedback

            return true;
        }

        // Expose API for programmatic error handling
        return {
            provide: {
                errorHandler: {
                    handle: handleError,
                    parseApiError,
                    isApiError,
                    isNetworkError,
                    ERROR_TYPES,
                },
            },
        };
    },
});
