/**
 * Application Configuration
 *
 * This is the ONLY file that needs to be modified to adapt the frontend to different data schemas.
 * The system will auto-discover the database schema and generate navigation based on this config
 * combined with the actual database foreign key relationships.
 */

/**
 * Core application settings - modify these for different deployments
 */
export const APP_CONFIG = {
    /**
     * The main entity table name (source of truth for all data)
     * This table should contain foreign keys to all navigation entities
     */
    mainTable: "datasets" as const,

    /**
     * Application branding and metadata
     */
    branding: {
        title: "FCC Physics Datasets",
        description: "Search and explore FCC physics simulation datasets and data",
        defaultTitle: "FCC Physics Datasets Search",
    },

    /**
     * API configuration
     */
    api: {
        baseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
        timeout: 30000,
    },

    /**
     * Authentication configuration
     */
    auth: {
        cookieName: "fcc-physics-events-web",
    },

    /**
     * Navigation order - will be fetched dynamically from backend
     * This is just a placeholder for type safety
     */
    navigationOrder: [] as readonly string[],

    /**
     * Navigation configuration - will be fetched dynamically from backend
     * This is just a placeholder structure for type safety
     */
    navigationMenu: {} as Record<
        string,
        {
            icon: string;
            label: string;
            badgeColor: "primary" | "neutral" | "success" | "warning" | "info" | "error";
            description: string;
        }
    >,

    /**
     * Search and pagination settings
     */
    search: {
        defaultPageSize: 20,
        maxPageSize: 100,
        debounceMs: 300,
    },

    /**
     * UI configuration
     */
    ui: {
        defaultBadgeColors: ["primary", "neutral", "success", "warning", "info", "error"] as const,
        // Use folder icon for all navigation items
        defaultIcon: "i-heroicons-folder" as const,
    },
} as const;

/**
 * Type definitions derived from config
 */
export type MainTableType = typeof APP_CONFIG.mainTable;

/**
 * Type for navigation keys that will be dynamically determined
 */
export type NavigationKey = string;
export type BadgeColor = (typeof APP_CONFIG.ui.defaultBadgeColors)[number];
