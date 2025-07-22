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
     * Navigation order - explicitly defines the hierarchy
     * This overrides any database-determined order
     */
    navigationOrder: ["accelerator", "stage", "campaign", "detector"] as const,

    /**
     * Navigation configuration overrides
     * If not specified, the system will auto-generate based on database schema
     * Keys should match foreign key column names (without _id suffix)
     */
    navigationOverrides: {
        accelerator: {
            icon: "i-heroicons-bolt",
            label: "Accelerator",
            badgeColor: "neutral" as const,
            description: "Type of particle accelerator used",
        },
        stage: {
            icon: "i-heroicons-cpu-chip",
            label: "Stage",
            badgeColor: "success" as const,
            description: "Processing stage of the dataset",
        },
        campaign: {
            icon: "i-heroicons-calendar-days",
            label: "Campaign",
            badgeColor: "warning" as const,
            description: "Data collection campaign",
        },
        detector: {
            icon: "i-heroicons-beaker",
            label: "Detector",
            badgeColor: "info" as const,
            description: "Detection equipment configuration",
        },
    } as const,

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
        defaultIcons: [
            "i-heroicons-squares-2x2",
            "i-heroicons-tag",
            "i-heroicons-folder",
            "i-heroicons-document",
            "i-heroicons-cube",
            "i-heroicons-beaker",
        ] as const,
    },
} as const;

/**
 * Type definitions derived from config
 */
export type MainTableType = typeof APP_CONFIG.mainTable;
export type NavigationKey = keyof typeof APP_CONFIG.navigationOverrides;
export type BadgeColor = (typeof APP_CONFIG.ui.defaultBadgeColors)[number];
