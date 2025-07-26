/**
 * Performance Optimization Utilities for Entity Metadata
 *
 * This composable provides core optimization utilities that are applied
 * universally to all entity metadata processing for consistent performance.
 */

// Constants for optimization behaviors (always applied)
export const PERFORMANCE_CONFIG = {
    // Batch size for processing
    BATCH_SIZE: 10,
} as const;

/**
 * Performance optimization composable - optimizations are always applied
 */
export const usePerformanceOptimizations = () => {
    /**
     * Debounced function creator for expensive operations
     */
    const createDebouncedFunction = <T extends (...args: any[]) => any>(fn: T, delay: number = 300): T => {
        let timeoutId: NodeJS.Timeout;

        return ((...args: Parameters<T>) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => fn(...args), delay);
        }) as T;
    };

    /**
     * Memoization utility for expensive computations
     */
    const createMemoizedFunction = <T extends (...args: any[]) => any>(
        fn: T,
        keyGenerator?: (...args: Parameters<T>) => string,
    ) => {
        const cache = new Map<string, ReturnType<T>>();

        return ((...args: Parameters<T>): ReturnType<T> => {
            const key = keyGenerator ? keyGenerator(...args) : JSON.stringify(args);

            if (cache.has(key)) {
                return cache.get(key)!;
            }

            const result = fn(...args);
            cache.set(key, result);

            // Limit cache size to prevent memory leaks
            if (cache.size > 100) {
                const firstKey = cache.keys().next().value as string;
                cache.delete(firstKey);
            }

            return result;
        }) as T;
    };

    /**
     * Batch processor for large arrays
     */
    const processBatches = async <T, R>(
        items: T[],
        processor: (batch: T[]) => Promise<R[]> | R[],
        batchSize: number = PERFORMANCE_CONFIG.BATCH_SIZE,
    ): Promise<R[]> => {
        const results: R[] = [];

        for (let i = 0; i < items.length; i += batchSize) {
            const batch = items.slice(i, i + batchSize);
            const batchResults = await processor(batch);
            results.push(...batchResults);

            // Allow other tasks to run between batches
            if (i + batchSize < items.length) {
                await new Promise((resolve) => setTimeout(resolve, 0));
            }
        }

        return results;
    };

    /**
     * Create a throttled version of a function
     */
    const createThrottledFunction = <T extends (...args: any[]) => any>(fn: T, delay: number = 100): T => {
        let lastCall = 0;

        return ((...args: Parameters<T>) => {
            const now = Date.now();
            if (now - lastCall >= delay) {
                lastCall = now;
                return fn(...args);
            }
        }) as T;
    };

    /**
     * Lazy evaluation utility for expensive computations
     */
    const lazy = <T>(factory: () => T): (() => T) => {
        let value: T;
        let hasValue = false;

        return () => {
            if (!hasValue) {
                value = factory();
                hasValue = true;
            }
            return value;
        };
    };

    return {
        // Core utilities (always applied)
        createDebouncedFunction,
        createMemoizedFunction,
        createThrottledFunction,
        processBatches,
        lazy,
    };
};
