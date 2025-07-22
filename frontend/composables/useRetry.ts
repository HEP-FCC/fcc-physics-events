/**
 * Retry utility with exponential backoff
 * Similar to Python's tenacity library
 */

export interface RetryOptions {
    /** Maximum number of retry attempts (default: 3) */
    maxAttempts?: number;
    /** Initial delay in milliseconds (default: 1000) */
    initialDelay?: number;
    /** Maximum delay in milliseconds (default: 30000) */
    maxDelay?: number;
    /** Backoff multiplier (default: 2) */
    backoffMultiplier?: number;
    /** Jitter to add randomness to delays (default: true) */
    useJitter?: boolean;
    /** Function to determine if error should trigger retry */
    shouldRetry?: (error: Error) => boolean;
}

export interface RetryResult<T> {
    /** The result of the successful operation */
    result: T;
    /** Number of attempts made */
    attempts: number;
    /** Total time spent retrying in milliseconds */
    totalTime: number;
}

/**
 * Default retry condition - retries on network errors and 5xx server errors
 */
const defaultShouldRetry = (error: Error): boolean => {
    // Network/connection errors
    if (
        error.message.includes("fetch failed") ||
        error.message.includes("Failed to fetch") ||
        error.message.includes("Network Error")
    ) {
        return true;
    }

    // Server errors (5xx)
    if ("status" in error && typeof error.status === "number") {
        return error.status >= 500 && error.status < 600;
    }

    return false;
};

/**
 * Calculate delay with exponential backoff and optional jitter
 */
function calculateDelay(
    attempt: number,
    initialDelay: number,
    maxDelay: number,
    backoffMultiplier: number,
    useJitter: boolean,
): number {
    const exponentialDelay = initialDelay * Math.pow(backoffMultiplier, attempt - 1);
    const delayWithCap = Math.min(exponentialDelay, maxDelay);

    if (useJitter) {
        // Add random jitter between 0% and 25% of the delay
        const jitter = delayWithCap * 0.25 * Math.random();
        return delayWithCap + jitter;
    }

    return delayWithCap;
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Retry an async operation with exponential backoff
 *
 * @param operation - The async operation to retry
 * @param options - Retry configuration options
 * @returns Promise that resolves with the result and retry metadata
 *
 * @example
 * ```typescript
 * const result = await retryWithBackoff(
 *   () => fetch('/api/data'),
 *   {
 *     maxAttempts: 5,
 *     initialDelay: 1000,
 *     maxDelay: 10000,
 *     shouldRetry: (error) => error.message.includes('timeout')
 *   }
 * );
 * ```
 */
export async function retryWithBackoff<T>(
    operation: () => Promise<T>,
    options: RetryOptions = {},
): Promise<RetryResult<T>> {
    const {
        maxAttempts = 3,
        initialDelay = 1000,
        maxDelay = 30000,
        backoffMultiplier = 2,
        useJitter = true,
        shouldRetry = defaultShouldRetry,
    } = options;

    const startTime = Date.now();
    let lastError: Error = new Error("Unknown error");

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            const result = await operation();
            return {
                result,
                attempts: attempt,
                totalTime: Date.now() - startTime,
            };
        } catch (error) {
            lastError = error instanceof Error ? error : new Error(String(error));

            // Don't retry on the last attempt or if error shouldn't trigger retry
            if (attempt === maxAttempts || !shouldRetry(lastError)) {
                break;
            }

            const delay = calculateDelay(attempt, initialDelay, maxDelay, backoffMultiplier, useJitter);

            // Log retry attempt for debugging
            if (import.meta.dev) {
                console.warn(
                    `Retry attempt ${attempt}/${maxAttempts} failed:`,
                    lastError.message,
                    `Retrying in ${Math.round(delay)}ms...`,
                );
            }

            await sleep(delay);
        }
    }

    // Enhance error with retry metadata
    const enhancedError = new Error(`Operation failed after ${maxAttempts} attempts: ${lastError.message}`) as Error & {
        originalError?: Error;
        attempts?: number;
        totalTime?: number;
        status?: number;
    };

    enhancedError.originalError = lastError;
    enhancedError.attempts = maxAttempts;
    enhancedError.totalTime = Date.now() - startTime;

    // Preserve status code if available
    if ("status" in lastError) {
        enhancedError.status = lastError.status as number;
    }

    throw enhancedError;
}

/**
 * Composable for retry functionality
 * Provides pre-configured retry functions for common use cases
 */
export function useRetry() {
    /**
     * Retry with default settings suitable for API calls
     */
    const retryApiCall = <T>(operation: () => Promise<T>) =>
        retryWithBackoff(operation, {
            maxAttempts: 3,
            initialDelay: 1000,
            maxDelay: 10000,
            useJitter: true,
        });

    /**
     * Retry with more aggressive settings for critical operations
     */
    const retryWithAggressive = <T>(operation: () => Promise<T>) =>
        retryWithBackoff(operation, {
            maxAttempts: 5,
            initialDelay: 500,
            maxDelay: 30000,
            backoffMultiplier: 2.5,
            useJitter: true,
        });

    /**
     * Retry with conservative settings for background operations
     */
    const retryWithConservative = <T>(operation: () => Promise<T>) =>
        retryWithBackoff(operation, {
            maxAttempts: 2,
            initialDelay: 2000,
            maxDelay: 8000,
            useJitter: false,
        });

    return {
        retryWithBackoff,
        retryApiCall,
        retryWithAggressive,
        retryWithConservative,
    };
}
