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
    mainTable: "entities" as const,

    /**
     * Application branding and metadata
     */
    branding: {
        title: "FCC Physics Data",
        appTitle: "FCC Physics Events",
        description: "Search and explore FCC physics simulation data and entities",
        defaultTitle: "FCC Physics Data Search",
    },

    /**
     * API configuration
     */
    api: {
        baseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
        timeout: 30000,
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
            description: string;
        }
    >,

    /**
     * Search and infinite scroll settings
     */
    search: {
        defaultPageSize: 25,
        maxPageSize: 1000,
    },

    /**
     * UI configuration
     */
    ui: {
        defaultBadgeColors: ["energy"] as const,
        // Use folder icon for all navigation items
        defaultIcon: "i-heroicons-folder" as const,
    },

    /**
     * Metadata preferences configuration
     */
    metadata: {
        // Default metadata fields to display as badges/tags
        defaultSelectedFields: ["n-events", "cross-section", "matching-eff"] as const,
    },

    /**
     * File download configuration
     */
    downloads: {
        // Prefix for downloaded file names
        fileNamePrefix: "fcc_physics_entities" as const,
    },

    /**
     * Navigation configuration fallbacks
     * Used when backend navigation config is not available
     */
    navigationFallback: {
        // Common navigation types in expected order
        order: ["accelerator", "stage", "campaign", "detector", "file_type"] as const,
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
export type BadgeColor =
    | (typeof APP_CONFIG.ui.defaultBadgeColors)[number]
    | "primary"
    | "neutral"
    | "success"
    | "warning"
    | "info"
    | "error"
    | "eco"
    | "earth"
    | "radiant-blue"
    | "space"
    | "flash"
    | "energy"
    | "deep-blue";
