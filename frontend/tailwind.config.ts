/**
 * Tailwind CSS Configuration
 *
 * Thi            // Typography enhancements
            fontFamily: {
                sans: ["Roobert", "Inter", "system-ui", "sans-serif"],
                display: ["Roobert", "Inter", "system-ui", "sans-serif"],
                body: ["Roobert", "Inter", "system-ui", "sans-serif"],
                mono: ["Space Mono", "Fira Code", "Consolas", "monospace"],
            },guration extends Tailwind CSS with our custom color design tokens.
 * It ensures that all our color palettes are available as Tailwind utilities.
 */

import type { Config } from "tailwindcss";
import { TAILWIND_COLORS } from "./config/colors";

export default {
    content: [
        "./components/**/*.{js,vue,ts}",
        "./layouts/**/*.vue",
        "./pages/**/*.vue",
        "./plugins/**/*.{js,ts}",
        "./app.vue",
        "./error.vue",
    ],
    theme: {
        extend: {
            colors: {
                // Our custom color system
                ...TAILWIND_COLORS,

                // Data visualization colors (accessible via data-energy-500, etc.)
                "data-energy": TAILWIND_COLORS.data.energy,
                "data-space": TAILWIND_COLORS.data.space,
                "data-flash": TAILWIND_COLORS.data.flash,
                "data-earth": TAILWIND_COLORS.data.earth,
                "data-eco": TAILWIND_COLORS.data.eco,
                "data-deep-blue": TAILWIND_COLORS.data.deepBlue,
                "data-radiant-blue": TAILWIND_COLORS.data.radiantBlue,
            },

            // Custom spacing based on our design system
            spacing: {
                energy: "0.5rem",
                space: "1rem",
                flash: "0.25rem",
                earth: "2rem",
            },

            // Typography enhancements
            fontFamily: {
                sans: ["Roobert", "Arial", "system-ui", "sans-serif"],
                display: ["Roobert", "Arial", "system-ui", "sans-serif"],
                body: ["Roobert", "Arial", "system-ui", "sans-serif"],
                mono: ["Space Mono", "Fira Code", "Consolas", "monospace"],
            },

            // Custom shadows using our color palette
            boxShadow: {
                energy: "0 4px 14px 0 rgba(144, 61, 255, 0.15)",
                space: "0 4px 14px 0 rgba(190, 230, 243, 0.25)",
                flash: "0 4px 14px 0 rgba(237, 253, 93, 0.25)",
                earth: "0 4px 14px 0 rgba(156, 130, 109, 0.15)",
                eco: "0 4px 14px 0 rgba(119, 135, 0, 0.15)",
                deep: "0 8px 32px 0 rgba(15, 18, 74, 0.3)",
                radiant: "0 4px 14px 0 rgba(0, 0, 255, 0.2)",
            },

            // Custom border radius
            borderRadius: {
                energy: "0.5rem",
                space: "1rem",
                flash: "0.25rem",
                earth: "0.75rem",
            },

            // Animation and transitions
            animation: {
                "fade-in": "fadeIn 0.5s ease-in-out",
                "slide-up": "slideUp 0.3s ease-out",
                "pulse-energy": "pulseEnergy 2s infinite",
            },

            keyframes: {
                fadeIn: {
                    "0%": { opacity: "0" },
                    "100%": { opacity: "1" },
                },
                slideUp: {
                    "0%": { transform: "translateY(10px)", opacity: "0" },
                    "100%": { transform: "translateY(0)", opacity: "1" },
                },
                pulseEnergy: {
                    "0%, 100%": { opacity: "1" },
                    "50%": { opacity: "0.8" },
                },
            },
        },
    },

    // Dark mode configuration
    darkMode: ["class", '[data-theme="dark"]'],

    plugins: [
        // Add any additional Tailwind plugins here
    ],
} satisfies Config;
