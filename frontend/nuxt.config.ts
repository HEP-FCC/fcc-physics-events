export default defineNuxtConfig({
    compatibilityDate: "2025-05-15",

    // Enable CSR mode for better search application performance
    ssr: false,

    colorMode: {
        preference: "light",
    },

    modules: ["@nuxt/eslint", "@nuxt/fonts", "@nuxt/icon", "@nuxt/image", "@nuxt/scripts", "@nuxt/ui"],
    css: ["assets/css/main.css"],

    // Ensure components in subdirectories are auto-imported
    components: [
        {
            path: "~/components",
            pathPrefix: false,
        },
    ],

    runtimeConfig: {
        public: {
            apiBaseUrl: process.env.BACKEND_URL || "http://localhost:8000",
        },
    },

    // Fix for module resolution issues
    vite: {
        optimizeDeps: {
            exclude: ["@nuxt/kit"],
        },
    },

    // Performance optimizations for CSR
    experimental: {
        payloadExtraction: false,
    },

    // App configuration
    app: {
        head: {
            viewport: "width=device-width,initial-scale=1",
            charset: "utf-8",
        },
    },
});
