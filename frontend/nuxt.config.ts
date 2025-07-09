// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
    compatibilityDate: "2025-05-15",
    devtools: { enabled: true },

    modules: ["@nuxt/eslint", "@nuxt/fonts", "@nuxt/icon", "@nuxt/image", "@nuxt/scripts", "@nuxt/ui"],
    css: ["assets/css/main.css"],

    runtimeConfig: {
        // Private config that is only available on the server

        // Public config that is available on both server and client
        public: {
            apiBaseUrl: process.env.BACKEND_URL || "http://localhost:8000",
        },
    },

    // Add this vite configuration for better file system watching in Docker
    vite: {
        server: {
            watch: {
                usePolling: true,
                interval: 100,
            },
        },
    },
});
