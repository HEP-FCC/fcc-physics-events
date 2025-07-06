/**
 * Navigation-related types for the FCC Physics frontend.
 * All types related to navigation dropdowns, menus, and UI controls.
 */

/**
 * Structure for dropdown menu items in navigation.
 */
export interface DropdownItem {
    id: number;
    name: string;
}

// Re-export types from the navigation composable
// This ensures all navigation types come from a single source of truth
export type { DropdownType } from "../composables/useNavigationConfig";
