/**
 * Composable for providing search field autocomplete suggestions
 * Integrates with the query language parser to provide context-aware suggestions
 */

interface SuggestionItem {
    value: string;
    type: "field" | "operator" | "value";
    description?: string;
}

interface AutocompleteState {
    suggestions: SuggestionItem[];
    isVisible: boolean;
    selectedIndex: number;
    triggerPosition: number;
}

export const useSearchAutocomplete = () => {
    const { getSortingFields } = useApiClient();

    // State
    const state = reactive<AutocompleteState>({
        suggestions: [],
        isVisible: false,
        selectedIndex: -1,
        triggerPosition: 0,
    });

    // Cache for field names
    const fieldNames = ref<string[]>([]);
    const fieldsLoaded = ref(false);

    // Operators that can be suggested
    const operators = [
        { value: "=", description: "equals" },
        { value: "!=", description: "not equals" },
        { value: ">", description: "greater than" },
        { value: "<", description: "less than" },
        { value: ">=", description: "greater than or equal" },
        { value: "<=", description: "less than or equal" },
        { value: ":", description: "contains (substring)" },
        { value: "=~", description: "regex match" },
        { value: "!~", description: "regex not match" },
        { value: "#", description: "fuzzy match (0.7 similarity)" },
        { value: ":*", description: "field exists" },
    ];

    // Boolean operators
    const booleanOperators = [
        { value: "AND", description: "logical AND" },
        { value: "OR", description: "logical OR" },
        { value: "NOT", description: "logical NOT" },
    ];

    /**
     * Load available field names from the API
     */
    const loadFieldNames = async () => {
        if (fieldsLoaded.value) return;

        try {
            const response = await getSortingFields();
            if (response.fields && response.fields.length > 0) {
                fieldNames.value = response.fields;
                fieldsLoaded.value = true;
            }
        } catch (error) {
            console.warn("Failed to load field names for autocomplete:", error);
        }
    };
    /**
     * Analyze the query context at cursor position to determine what to suggest
     */
    const analyzeQueryContext = (
        query: string,
        cursorPosition: number,
    ): "field" | "operator" | "value" | "boolean" | null => {
        const beforeCursor = query.slice(0, cursorPosition);
        const afterCursor = query.slice(cursorPosition);

        // If we're at the beginning or after AND/OR/NOT, suggest fields
        if (beforeCursor.trim() === "" || /\b(AND|OR|NOT)\s*$/i.test(beforeCursor)) {
            return "field";
        }

        // If we have a field name followed by space, suggest operators
        const fieldPattern = /\w+\s*$/;
        if (fieldPattern.test(beforeCursor) && !beforeCursor.includes("=") && !beforeCursor.includes(":")) {
            return "operator";
        }

        // If we have field + operator, suggest values (for specific fields) or boolean operators
        const fieldOperatorPattern = /\w+\s*[=!<>:~]+\s*"?[^"]*"?\s*$/;
        if (fieldOperatorPattern.test(beforeCursor)) {
            return "boolean";
        }

        // If we're in the middle of typing a field name, suggest fields
        const partialFieldPattern = /(?:^|\s|\()([\w.]+)$/;
        const match = beforeCursor.match(partialFieldPattern);
        if (match) {
            return "field";
        }

        return null;
    };

    /**
     * Filter field names based on partial input
     */
    const filterFields = (partial: string): SuggestionItem[] => {
        if (!partial)
            return fieldNames.value.slice(0, 10).map((field) => ({
                value: field,
                type: "field" as const,
                description: getFieldDescription(field),
            }));

        const filtered = fieldNames.value.filter((field) => field.toLowerCase().includes(partial.toLowerCase()));

        // Sort by relevance (exact match, starts with, contains)
        filtered.sort((a, b) => {
            const aLower = a.toLowerCase();
            const bLower = b.toLowerCase();
            const partialLower = partial.toLowerCase();

            if (aLower === partialLower) return -1;
            if (bLower === partialLower) return 1;
            if (aLower.startsWith(partialLower)) return -1;
            if (bLower.startsWith(partialLower)) return 1;
            return 0;
        });

        return filtered.slice(0, 10).map((field) => ({
            value: field,
            type: "field" as const,
            description: getFieldDescription(field),
        }));
    };

    /**
     * Get a description for a field name
     */
    const getFieldDescription = (field: string): string => {
        if (field.startsWith("metadata.")) {
            return "Metadata field";
        }
        if (field.endsWith("_name")) {
            return "Related entity name";
        }
        if (field.endsWith("_id")) {
            return "Entity ID";
        }
        if (field.includes("date") || field.includes("time")) {
            return "Date/time field";
        }
        return "Database field";
    };

    /**
     * Analyze the query context to determine what type of suggestion to show
     */
    const analyzeContext = (beforeCursor: string): "field" | "operator" | "value" => {
        const trimmed = beforeCursor.trim();

        // If empty or starts with boolean operator, suggest field names
        if (!trimmed || /\b(AND|OR|NOT)\s*$/i.test(trimmed)) {
            return "field";
        }

        // If after opening parenthesis, suggest field names
        if (/\(\s*$/.test(trimmed)) {
            return "field";
        }

        // Check for boolean operators followed by potential field start (including hyphens)
        if (/\b(AND|OR|NOT)\s+[\w.-]*$/i.test(trimmed)) {
            return "field";
        }

        // Split by AND/OR/NOT to get the current segment we're working on
        const segments = trimmed.split(/\b(AND|OR|NOT)\b/i);
        const currentSegment = segments[segments.length - 1].trim();

        // If current segment is empty, suggest fields
        if (!currentSegment) {
            return "field";
        }

        // Check if current segment has field + operator + value pattern
        const valuePattern = /([\w.-]+)\s*([><=!:~]+)\s*([^)\s]+)$/i;
        const valueMatch = valuePattern.exec(currentSegment);

        if (valueMatch) {
            const fieldName = valueMatch[1];
            const operator = valueMatch[2];
            const valueStart = valueMatch[3];

            // If we have field + operator + some value content, we're in value context
            if (operator && valueStart && valueStart.length > 0) {
                return "value";
            }
        }

        // Check if current segment has field + operator but no value yet
        const fieldOperatorPattern = /([\w.-]+)\s*([><=!:~]+)\s*$/i;
        const fieldOpMatch = fieldOperatorPattern.exec(currentSegment);

        if (fieldOpMatch) {
            // We have field + operator but no value yet, ready for value input
            return "value";
        }

        // Check for field name pattern in current segment
        const fieldOnlyPattern = /([\w.-]+)(\s*)$/i;
        const fieldMatch = fieldOnlyPattern.exec(currentSegment);

        if (fieldMatch) {
            const fieldName = fieldMatch[1];
            const hasSpaceAfter = fieldMatch[2].length > 0;

            // Check if the field name exists in our field list (exact match)
            const exactMatch = fieldNames.value.some((f) => f.toLowerCase() === fieldName.toLowerCase());

            // Check if it's a close match (for fields like "nevents" vs "n-events")
            const closeMatches = fieldNames.value.filter((f) => {
                const fLower = f.toLowerCase();
                const fieldLower = fieldName.toLowerCase();

                // Check various formats: n-events, nevents, n_events, etc.
                const normalizedField = fieldLower.replace(/[-_]/g, "");
                const normalizedAvailable = fLower.replace(/[-_]/g, "");

                return fLower === fieldLower || normalizedField === normalizedAvailable;
            });

            // Only suggest operators if we have an EXACT match AND space after
            if (exactMatch && hasSpaceAfter) {
                return "operator";
            }
            // If exact match but no space, suggest operators (user just finished typing field name)
            else if (exactMatch && !hasSpaceAfter) {
                return "operator";
            }
            // If close match and space after, suggest operators
            else if (closeMatches.length > 0 && hasSpaceAfter) {
                return "operator";
            }
            // Otherwise, suggest field completions (partial typing)
            else {
                return "field";
            }
        }

        // Default to field suggestions
        return "field";
    };

    /**
     * Get suggestions based on current query and cursor position
     */
    const getSuggestions = async (query: string, cursorPosition: number): Promise<SuggestionItem[]> => {
        if (!fieldsLoaded.value) {
            await loadFieldNames();
        }

        const beforeCursor = query.slice(0, cursorPosition);
        const context = analyzeContext(beforeCursor);
        const suggestions: SuggestionItem[] = [];

        if (context === "field") {
            // Extract partial field name (including hyphens)
            const fieldMatch = beforeCursor.match(/(?:^|\s|\(|AND\s+|OR\s+|NOT\s+)([\w.-]*)$/i);
            const partial = fieldMatch ? fieldMatch[1] : "";

            // Get field suggestions
            const fieldSuggestions = filterFields(partial);
            suggestions.push(...fieldSuggestions);
        } else if (context === "operator") {
            // Add operator suggestions
            operators.forEach((op) => {
                suggestions.push({
                    value: op.value,
                    type: "operator" as const,
                    description: op.description,
                });
            });
        } else if (context === "value") {
            // When in value context, don't show any suggestions
            // User should be able to type freely without autocomplete interference
            return [];
        }

        return suggestions.slice(0, 10); // Limit to 10 suggestions
    };

    /**
     * Show suggestions for the given query and cursor position
     */
    const showSuggestions = async (query: string, cursorPosition: number) => {
        const suggestions = await getSuggestions(query, cursorPosition);

        state.suggestions = suggestions;
        state.isVisible = suggestions.length > 0;
        state.selectedIndex = suggestions.length > 0 ? 0 : -1;
        state.triggerPosition = cursorPosition;
    };

    /**
     * Hide suggestions
     */
    const hideSuggestions = () => {
        state.isVisible = false;
        state.suggestions = [];
        state.selectedIndex = -1;
    };

    /**
     * Navigate through suggestions
     */
    const navigateSuggestions = (direction: "up" | "down") => {
        if (!state.isVisible || state.suggestions.length === 0) return;

        if (direction === "up") {
            state.selectedIndex = state.selectedIndex <= 0 ? state.suggestions.length - 1 : state.selectedIndex - 1;
        } else {
            state.selectedIndex = state.selectedIndex >= state.suggestions.length - 1 ? 0 : state.selectedIndex + 1;
        }
    };

    /**
     * Get the currently selected suggestion
     */
    const getSelectedSuggestion = (): SuggestionItem | null => {
        if (state.selectedIndex >= 0 && state.selectedIndex < state.suggestions.length) {
            return state.suggestions[state.selectedIndex];
        }
        return null;
    };

    /**
     * Apply a suggestion to the query
     */
    const applySuggestion = (
        query: string,
        cursorPosition: number,
        suggestion: SuggestionItem,
    ): { newQuery: string; newCursorPosition: number } => {
        const beforeCursor = query.slice(0, cursorPosition);
        const afterCursor = query.slice(cursorPosition);

        let newQuery: string;
        let newCursorPosition: number;

        if (suggestion.type === "field") {
            // For field suggestions, replace the partial field name being typed (including hyphens)
            const fieldMatch = beforeCursor.match(/(?:^|\s|\(|AND\s+|OR\s+|NOT\s+)([\w.-]*)$/i);
            if (fieldMatch) {
                // We found a partial field pattern, replace it
                const partialField = fieldMatch[1];
                const replaceStart = cursorPosition - partialField.length;
                newQuery = query.slice(0, replaceStart) + suggestion.value + afterCursor;
                newCursorPosition = replaceStart + suggestion.value.length;
            } else {
                // No partial field found, just append
                newQuery = beforeCursor + suggestion.value + afterCursor;
                newCursorPosition = cursorPosition + suggestion.value.length;
            }
        } else if (suggestion.type === "operator") {
            // Add operator with appropriate spacing
            const needsSpaceBefore = beforeCursor.trim() !== "" && !beforeCursor.endsWith(" ");
            const needsSpaceAfter = ![":", ":*"].includes(suggestion.value);

            const prefix = needsSpaceBefore ? " " : "";
            const suffix = needsSpaceAfter ? " " : "";

            newQuery = beforeCursor + prefix + suggestion.value + suffix + afterCursor;
            newCursorPosition = cursorPosition + prefix.length + suggestion.value.length + suffix.length;
        } else {
            // Default case for other types
            newQuery = beforeCursor + suggestion.value + afterCursor;
            newCursorPosition = cursorPosition + suggestion.value.length;
        }

        return { newQuery, newCursorPosition };
    };

    /**
     * Set the selected index directly
     */
    const setSelectedIndex = (index: number) => {
        state.selectedIndex = index;
    };

    return {
        state: readonly(state),
        showSuggestions,
        hideSuggestions,
        navigateSuggestions,
        getSelectedSuggestion,
        applySuggestion,
        loadFieldNames,
        setSelectedIndex,
    };
};
