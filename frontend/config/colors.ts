/**
 * Color Design Tokens Configuration
 *
 * This module defines all color tokens for the FCC Physics Events frontend application.
 * The structure follows design token best practices and W3C Design Tokens Community Group specifications.
 *
 * Organization:
 * - Semantic color tokens (what they represent)
 * - Primitive color tokens (the actual color values)
 * - Theme-specific configurations (light/dark modes)
 *
 * Color palettes are organized by their conceptual meaning:
 * - ENERGY: Primary branding and interactive elements
 * - SPACE: Background and surface colors
 * - FLASH: Accent and highlight colors
 * - EARTH: Natural and grounding elements
 * - ECO: Success and environmental states
 * - DEEP_BLUE: Dark theme foundation
 * - RADIANT_BLUE: Pure blue spectrum for data visualization
 */

// =============================================================================
// PRIMITIVE COLOR TOKENS
// These are the foundational color values that never change
// =============================================================================

export const PRIMITIVE_COLORS = {
    // ENERGY Palette - Primary branding and interactive elements
    energy: {
        main: "#903dff",
        50: "#d1bcfc", // lightest
        100: "#bba1fb",
        200: "#a585fa",
        300: "#9069f8",
        400: "#7a4df6",
        500: "#903dff", // main color
        600: "#7a35e6",
        700: "#642ccc",
        800: "#4e24b3",
        900: "#381b99", // darkest computed
    },

    // SPACE Palette - Background and surface colors
    space: {
        main: "#bee6f3",
        50: "#e6f4fa", // lightest
        100: "#d9eff8",
        200: "#cceaf6",
        300: "#c0e5f5",
        400: "#b4e0f4",
        500: "#bee6f3", // main color
        600: "#a8d1de",
        700: "#92bcc9",
        800: "#7ca7b4",
        900: "#66929f", // darkest computed
    },

    // FLASH Palette - Accent and highlight colors
    flash: {
        main: "#edfd5d",
        50: "#f8fee8", // lightest
        100: "#f4fecf",
        200: "#f0fdb6",
        300: "#ecfd9d",
        400: "#e8fc84",
        500: "#edfd5d", // main color
        600: "#d4e454",
        700: "#bbcb4b",
        800: "#a2b242",
        900: "#899939", // darkest computed
    },

    // EARTH Palette - Natural and grounding elements
    earth: {
        main: "#9c826d",
        50: "#dcd1c8", // lightest
        100: "#cebfb4",
        200: "#bfaea0",
        300: "#b19d8c",
        400: "#a38b78",
        500: "#9c826d", // main color
        600: "#8a735f",
        700: "#786451",
        800: "#665543",
        900: "#544635", // darkest computed
    },

    // ECO Palette - Success and environmental states
    eco: {
        main: "#778700",
        50: "#cdd499", // lightest
        100: "#b9c177",
        200: "#a6ad55",
        300: "#929a33",
        400: "#7e8711",
        500: "#778700", // main color
        600: "#6b7900",
        700: "#5f6b00",
        800: "#535d00",
        900: "#474f00", // darkest computed
    },

    // DEEP_BLUE Palette - Dark theme foundation
    deepBlue: {
        main: "#0f124a",
        50: "#a0a2b8", // lightest
        100: "#8184a1",
        200: "#63668a",
        300: "#464973",
        400: "#2a2d5c",
        500: "#0f124a", // main color
        600: "#0e1043",
        700: "#0c0e3c",
        800: "#0b0c35",
        900: "#090a2e", // darkest computed
    },

    // RADIANT_BLUE Palette - Pure blue spectrum for data visualization
    radiantBlue: {
        main: "#0000ff",
        50: "#ccccff", // lightest
        100: "#9999ff",
        200: "#6666ff",
        300: "#3333ff",
        400: "#0000e6",
        500: "#0000ff", // main color
        600: "#0000e6",
        700: "#0000cc",
        800: "#0000b3",
        900: "#000099", // darkest computed
    },

    // Utility colors
    neutral: {
        white: "#ffffff",
        black: "#000000",
        transparent: "transparent",
    },
} as const;

// =============================================================================
// SEMANTIC COLOR TOKENS
// These define what colors mean in the context of the application
// =============================================================================

export const SEMANTIC_COLORS = {
    // Primary brand colors
    primary: {
        50: PRIMITIVE_COLORS.energy[50],
        100: PRIMITIVE_COLORS.energy[100],
        200: PRIMITIVE_COLORS.energy[200],
        300: PRIMITIVE_COLORS.energy[300],
        400: PRIMITIVE_COLORS.energy[400],
        500: PRIMITIVE_COLORS.energy[500],
        600: PRIMITIVE_COLORS.energy[600],
        700: PRIMITIVE_COLORS.energy[700],
        800: PRIMITIVE_COLORS.energy[800],
        900: PRIMITIVE_COLORS.energy[900],
        DEFAULT: PRIMITIVE_COLORS.energy.main,
    },

    // Secondary colors for supporting elements
    secondary: {
        50: PRIMITIVE_COLORS.space[50],
        100: PRIMITIVE_COLORS.space[100],
        200: PRIMITIVE_COLORS.space[200],
        300: PRIMITIVE_COLORS.space[300],
        400: PRIMITIVE_COLORS.space[400],
        500: PRIMITIVE_COLORS.space[500],
        600: PRIMITIVE_COLORS.space[600],
        700: PRIMITIVE_COLORS.space[700],
        800: PRIMITIVE_COLORS.space[800],
        900: PRIMITIVE_COLORS.space[900],
        DEFAULT: PRIMITIVE_COLORS.space.main,
    },

    // Accent colors for highlights and calls-to-action
    accent: {
        50: PRIMITIVE_COLORS.flash[50],
        100: PRIMITIVE_COLORS.flash[100],
        200: PRIMITIVE_COLORS.flash[200],
        300: PRIMITIVE_COLORS.flash[300],
        400: PRIMITIVE_COLORS.flash[400],
        500: PRIMITIVE_COLORS.flash[500],
        600: PRIMITIVE_COLORS.flash[600],
        700: PRIMITIVE_COLORS.flash[700],
        800: PRIMITIVE_COLORS.flash[800],
        900: PRIMITIVE_COLORS.flash[900],
        DEFAULT: PRIMITIVE_COLORS.flash.main,
    },

    // Success states (using ECO palette)
    success: {
        50: PRIMITIVE_COLORS.eco[50],
        100: PRIMITIVE_COLORS.eco[100],
        200: PRIMITIVE_COLORS.eco[200],
        300: PRIMITIVE_COLORS.eco[300],
        400: PRIMITIVE_COLORS.eco[400],
        500: PRIMITIVE_COLORS.eco[500],
        600: PRIMITIVE_COLORS.eco[600],
        700: PRIMITIVE_COLORS.eco[700],
        800: PRIMITIVE_COLORS.eco[800],
        900: PRIMITIVE_COLORS.eco[900],
        DEFAULT: PRIMITIVE_COLORS.eco.main,
    },

    // Warning states (using FLASH palette)
    warning: {
        50: PRIMITIVE_COLORS.flash[50],
        100: PRIMITIVE_COLORS.flash[100],
        200: PRIMITIVE_COLORS.flash[200],
        300: PRIMITIVE_COLORS.flash[300],
        400: PRIMITIVE_COLORS.flash[400],
        500: PRIMITIVE_COLORS.flash[500],
        600: PRIMITIVE_COLORS.flash[600],
        700: PRIMITIVE_COLORS.flash[700],
        800: PRIMITIVE_COLORS.flash[800],
        900: PRIMITIVE_COLORS.flash[900],
        DEFAULT: PRIMITIVE_COLORS.flash.main,
    },

    // Error states (using computed red variants from energy palette)
    error: {
        50: "#fef2f2",
        100: "#fee2e2",
        200: "#fecaca",
        300: "#fca5a5",
        400: "#f87171",
        500: "#ef4444",
        600: "#dc2626",
        700: "#b91c1c",
        800: "#991b1b",
        900: "#7f1d1d",
        DEFAULT: "#ef4444",
    },

    // Information states (using RADIANT_BLUE palette)
    info: {
        50: PRIMITIVE_COLORS.radiantBlue[50],
        100: PRIMITIVE_COLORS.radiantBlue[100],
        200: PRIMITIVE_COLORS.radiantBlue[200],
        300: PRIMITIVE_COLORS.radiantBlue[300],
        400: PRIMITIVE_COLORS.radiantBlue[400],
        500: PRIMITIVE_COLORS.radiantBlue[500],
        600: PRIMITIVE_COLORS.radiantBlue[600],
        700: PRIMITIVE_COLORS.radiantBlue[700],
        800: PRIMITIVE_COLORS.radiantBlue[800],
        900: PRIMITIVE_COLORS.radiantBlue[900],
        DEFAULT: PRIMITIVE_COLORS.radiantBlue.main,
    },

    // Gray scale (using EARTH palette for natural feel)
    gray: {
        50: PRIMITIVE_COLORS.earth[50],
        100: PRIMITIVE_COLORS.earth[100],
        200: PRIMITIVE_COLORS.earth[200],
        300: PRIMITIVE_COLORS.earth[300],
        400: PRIMITIVE_COLORS.earth[400],
        500: PRIMITIVE_COLORS.earth[500],
        600: PRIMITIVE_COLORS.earth[600],
        700: PRIMITIVE_COLORS.earth[700],
        800: PRIMITIVE_COLORS.earth[800],
        900: PRIMITIVE_COLORS.earth[900],
        DEFAULT: PRIMITIVE_COLORS.earth.main,
    },

    // Data visualization colors (full spectrum available)
    data: {
        energy: PRIMITIVE_COLORS.energy,
        space: PRIMITIVE_COLORS.space,
        flash: PRIMITIVE_COLORS.flash,
        earth: PRIMITIVE_COLORS.earth,
        eco: PRIMITIVE_COLORS.eco,
        deepBlue: PRIMITIVE_COLORS.deepBlue,
        radiantBlue: PRIMITIVE_COLORS.radiantBlue,
    },

    // Utility colors
    white: PRIMITIVE_COLORS.neutral.white,
    black: PRIMITIVE_COLORS.neutral.black,
    transparent: PRIMITIVE_COLORS.neutral.transparent,
} as const;

// =============================================================================
// THEME CONFIGURATIONS
// Light and dark mode specific overrides
// =============================================================================

export const LIGHT_THEME = {
    background: {
        primary: PRIMITIVE_COLORS.neutral.white,
        secondary: PRIMITIVE_COLORS.space[50],
        tertiary: PRIMITIVE_COLORS.space[100],
    },
    surface: {
        primary: PRIMITIVE_COLORS.neutral.white,
        secondary: PRIMITIVE_COLORS.space[50],
        elevated: PRIMITIVE_COLORS.neutral.white,
    },
    text: {
        primary: PRIMITIVE_COLORS.deepBlue[500],
        secondary: PRIMITIVE_COLORS.deepBlue[400],
        tertiary: PRIMITIVE_COLORS.earth[600],
        inverse: PRIMITIVE_COLORS.neutral.white,
    },
    border: {
        primary: PRIMITIVE_COLORS.space[300],
        secondary: PRIMITIVE_COLORS.space[200],
        focus: PRIMITIVE_COLORS.energy[500],
    },
} as const;

export const DARK_THEME = {
    background: {
        primary: PRIMITIVE_COLORS.deepBlue[500],
        secondary: PRIMITIVE_COLORS.deepBlue[400],
        tertiary: PRIMITIVE_COLORS.deepBlue[300],
    },
    surface: {
        primary: PRIMITIVE_COLORS.deepBlue[400],
        secondary: PRIMITIVE_COLORS.deepBlue[300],
        elevated: PRIMITIVE_COLORS.deepBlue[300],
    },
    text: {
        primary: PRIMITIVE_COLORS.neutral.white,
        secondary: PRIMITIVE_COLORS.space[100],
        tertiary: PRIMITIVE_COLORS.space[200],
        inverse: PRIMITIVE_COLORS.deepBlue[500],
    },
    border: {
        primary: PRIMITIVE_COLORS.deepBlue[300],
        secondary: PRIMITIVE_COLORS.deepBlue[200],
        focus: PRIMITIVE_COLORS.energy[400],
    },
} as const;

// =============================================================================
// TAILWIND-COMPATIBLE COLOR CONFIGURATION
// This is what gets used in your Tailwind/Nuxt UI configuration
// =============================================================================

export const TAILWIND_COLORS = {
    ...SEMANTIC_COLORS,

    // Ensure compatibility with Nuxt UI defaults
    cool: SEMANTIC_COLORS.secondary,
    red: SEMANTIC_COLORS.error,
    orange: SEMANTIC_COLORS.warning,
    amber: SEMANTIC_COLORS.warning,
    yellow: SEMANTIC_COLORS.warning,
    lime: SEMANTIC_COLORS.success,
    green: SEMANTIC_COLORS.success,
    emerald: SEMANTIC_COLORS.success,
    teal: SEMANTIC_COLORS.secondary,
    cyan: SEMANTIC_COLORS.secondary,
    sky: SEMANTIC_COLORS.info,
    blue: SEMANTIC_COLORS.info,
    indigo: SEMANTIC_COLORS.primary,
    violet: SEMANTIC_COLORS.primary,
    purple: SEMANTIC_COLORS.primary,
    fuchsia: SEMANTIC_COLORS.accent,
    pink: SEMANTIC_COLORS.accent,
    rose: SEMANTIC_COLORS.error,
    slate: SEMANTIC_COLORS.gray,
    zinc: SEMANTIC_COLORS.gray,
    neutral: SEMANTIC_COLORS.gray,
    stone: SEMANTIC_COLORS.gray,
} as const;

// =============================================================================
// CSS CUSTOM PROPERTIES GENERATOR
// Generates CSS variables for use in stylesheets
// =============================================================================

export function generateCSSVariables() {
    const cssVars: Record<string, string> = {};

    // Generate CSS variables for all semantic colors
    Object.entries(SEMANTIC_COLORS).forEach(([key, value]) => {
        if (typeof value === "object" && value !== null) {
            Object.entries(value).forEach(([shade, color]) => {
                cssVars[`--color-${key}-${shade}`] = color;
            });
        } else {
            cssVars[`--color-${key}`] = value;
        }
    });

    // Generate theme-specific variables
    Object.entries(LIGHT_THEME).forEach(([category, colors]) => {
        Object.entries(colors).forEach(([key, color]) => {
            cssVars[`--theme-light-${category}-${key}`] = color;
        });
    });

    Object.entries(DARK_THEME).forEach(([category, colors]) => {
        Object.entries(colors).forEach(([key, color]) => {
            cssVars[`--theme-dark-${category}-${key}`] = color;
        });
    });

    return cssVars;
}

// =============================================================================
// UTILITY FUNCTIONS
// Helper functions for working with colors
// =============================================================================

/**
 * Get a specific color from a palette
 */
export function getColor(palette: keyof typeof PRIMITIVE_COLORS, shade: string | number = "main") {
    const paletteColors = PRIMITIVE_COLORS[palette];

    // Handle special case for neutral colors which don't have 'main' or numeric shades
    if (palette === "neutral") {
        if (shade === "main" || shade === "white") {
            return (paletteColors as typeof PRIMITIVE_COLORS.neutral).white;
        }
        if (shade === "black") {
            return (paletteColors as typeof PRIMITIVE_COLORS.neutral).black;
        }
        if (shade === "transparent") {
            return (paletteColors as typeof PRIMITIVE_COLORS.neutral).transparent;
        }
        // Default to white for any other shade
        return (paletteColors as typeof PRIMITIVE_COLORS.neutral).white;
    }

    // For other palettes that have main and numeric shades
    const colorPalette = paletteColors as any;
    return colorPalette[shade] || colorPalette.main;
}

/**
 * Get a semantic color
 */
export function getSemanticColor(semantic: keyof typeof SEMANTIC_COLORS, shade: string | number = "DEFAULT") {
    const semanticColors = SEMANTIC_COLORS[semantic];
    if (typeof semanticColors === "string") {
        return semanticColors;
    }

    // Handle the data object which contains nested color palettes
    if (semantic === "data") {
        return "#000000"; // Default fallback for data
    }

    // For color objects with shades, try to get the shade or fallback to DEFAULT
    const colorObj = semanticColors as any;
    return colorObj[shade] || colorObj.DEFAULT || colorObj["500"] || "#000000";
}

/**
 * Get theme-specific color
 */
export function getThemeColor(theme: "light" | "dark", category: string, key: string): string | undefined {
    const themeColors = theme === "light" ? LIGHT_THEME : DARK_THEME;
    const categoryColors = (themeColors as any)[category];
    if (categoryColors && typeof categoryColors === "object") {
        return categoryColors[key];
    }
    return undefined;
}

// =============================================================================
// TYPE DEFINITIONS
// TypeScript types for better development experience
// =============================================================================

export type PrimitiveColorPalette = keyof typeof PRIMITIVE_COLORS;
export type SemanticColorKey = keyof typeof SEMANTIC_COLORS;
export type ColorShade =
    | "50"
    | "100"
    | "200"
    | "300"
    | "400"
    | "500"
    | "600"
    | "700"
    | "800"
    | "900"
    | "DEFAULT"
    | "main";
export type ThemeMode = "light" | "dark";
export type ThemeCategory = keyof typeof LIGHT_THEME;

// =============================================================================
// EXPORTS
// =============================================================================

export default {
    primitive: PRIMITIVE_COLORS,
    semantic: SEMANTIC_COLORS,
    tailwind: TAILWIND_COLORS,
    themes: {
        light: LIGHT_THEME,
        dark: DARK_THEME,
    },
    utils: {
        getColor,
        getSemanticColor,
        getThemeColor,
        generateCSSVariables,
    },
};
