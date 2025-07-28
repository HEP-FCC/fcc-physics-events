import {
    formatFieldLabel,
    createEntityDownloadFilename,
    downloadAsJsonFile,
    formatFieldName,
    copyToClipboard,
    formatTimestamp,
    formatSizeInGiB,
    isStatusField,
    getStatusBadgeColor,
    getStatusFields,
} from "~/utils/formatting";

import type { Entity } from "~/types/api";

/**
 * Get primary key value from entity
 */
export function getPrimaryKeyValue(entity: Entity): number | null {
    return entity.dataset_id || null;
}

/**
 * Extract entity IDs from entity array
 */
export function extractEntityIds(entities: Entity[]): number[] {
    return entities.map((entity) => getPrimaryKeyValue(entity)).filter((id): id is number => id !== null);
}

/**
 * Retry function with exponential backoff
 */
export interface RetryOptions {
    maxAttempts?: number;
    baseDelay?: number;
    maxDelay?: number;
    backoffFactor?: number;
}

export async function retryWithBackoff<T>(operation: () => Promise<T>, options: RetryOptions = {}): Promise<T> {
    const { maxAttempts = 3, baseDelay = 1000, maxDelay = 10000, backoffFactor = 2 } = options;

    let lastError: Error;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            return await operation();
        } catch (error) {
            lastError = error as Error;

            if (attempt === maxAttempts) {
                throw lastError;
            }

            const delay = Math.min(baseDelay * Math.pow(backoffFactor, attempt - 1), maxDelay);
            await new Promise((resolve) => setTimeout(resolve, delay));
        }
    }

    throw lastError!;
}

/**
 * Composable for utility functions
 * Provides reactive versions of utility functions and manages state
 */
/**
 * Handle API errors with specific messaging for auth/authorization issues
 */
export function handleApiError(error: unknown, toast: any, login: () => void): boolean {
    // Parse structured error response from backend
    let errorDetails: { error?: string; message?: string; required_role?: string } = {};
    let statusCode = 0;

    if (error && typeof error === "object" && "details" in error) {
        errorDetails = (error as any).details || {};
        statusCode = (error as any).status || 0;
    } else if (error instanceof Error) {
        // Try to extract status code from error message
        const statusMatch = error.message.match(/(\d{3})/);
        statusCode = statusMatch ? parseInt(statusMatch[1]) : 0;
    }

    // Handle specific authentication and authorization errors
    if (statusCode === 401) {
        const errorType = errorDetails.error || "unknown";

        switch (errorType) {
            case "token_expired":
                toast.add({
                    title: "Session Expired",
                    description: "Your session has expired. Please login again.",
                    color: "warning",
                });
                break;
            case "invalid_token":
                toast.add({
                    title: "Authentication Error",
                    description: "Invalid authentication token. Please login again.",
                    color: "warning",
                });
                break;
            case "missing_token":
                toast.add({
                    title: "Authentication Required",
                    description: "Please login to access this resource.",
                    color: "warning",
                });
                break;
            default:
                toast.add({
                    title: "Authentication Required",
                    description: errorDetails.message || "Your session has expired. Please login again.",
                    color: "warning",
                });
        }
        login();
        return true; // Handled
    }

    if (statusCode === 403) {
        const errorType = errorDetails.error || "unknown";

        if (errorType === "missing_roles") {
            const requiredRole = errorDetails.required_role || "required permissions";
            toast.add({
                title: "Access Denied",
                description: `You are missing required roles (${requiredRole}) to perform this action. Please contact the website administrator for granting access to the resources.`,
                color: "error",
            });
        } else {
            toast.add({
                title: "Permission Denied",
                description: errorDetails.message || "You don't have permission to perform this action.",
                color: "error",
            });
        }
        return true; // Handled
    }

    return false; // Not handled, let the caller handle it
}

export function useUtils() {
    // Re-export utility functions for convenience
    return {
        // Pure utility functions (re-exported from utils)
        formatFieldLabel,
        createEntityDownloadFilename,
        downloadAsJsonFile,
        formatFieldName,
        copyToClipboard,
        formatTimestamp,
        formatSizeInGiB,
        isStatusField,
        getStatusBadgeColor,
        getStatusFields,

        // Entity utilities
        getPrimaryKeyValue,
        extractEntityIds,
        retryWithBackoff,

        // Error handling utilities
        handleApiError,
    };
}
