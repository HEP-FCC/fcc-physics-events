<template>
    <div class="relative">
        <UInput
            ref="inputRef"
            v-model="inputValue"
            :placeholder="placeholder"
            size="lg"
            icon="i-heroicons-magnifying-glass"
            :class="inputClass"
            @keydown="handleKeyDown"
            @input="handleInput"
            @focus="handleFocus"
            @blur="handleBlur"
            @click="handleClick"
        />

        <AutocompleteDropdown
            :suggestions="autocomplete.state.suggestions"
            :is-visible="autocomplete.state.isVisible"
            :selected-index="autocomplete.state.selectedIndex"
            :input-element="inputElement"
            :cursor-position="cursorPosition"
            @select="handleSuggestionSelect"
            @highlight="handleSuggestionHighlight"
        />
    </div>
</template>

<script setup lang="ts">
interface Props {
    modelValue: string;
    placeholder?: string;
    inputClass?: string;
}

interface Emits {
    (e: "update:modelValue", value: string): void;
    (e: "enter"): void;
    (e: "focus"): void;
    (e: "blur"): void;
}

const props = withDefaults(defineProps<Props>(), {
    placeholder: "Type to search...",
    inputClass: "pr-16 w-full",
});

const emit = defineEmits<Emits>();

// Imports
import AutocompleteDropdown from "./AutocompleteDropdown.vue";

// Composables
const autocomplete = useSearchAutocomplete();

// Refs
const inputRef = ref<HTMLInputElement | null>(null);
const cursorPosition = ref(0);
const showAutocompleteOnFocus = ref(false);
const isAutocompleteIntentional = ref(false);

// Computed
const inputValue = computed({
    get: () => props.modelValue,
    set: (value: string) => {
        emit("update:modelValue", value);
        updateCursorPosition();
    },
});

const inputElement = computed(() => {
    const element = inputRef.value;
    if (!element) return null;

    // For UInput component, we need to find the actual input element
    if ("$el" in element) {
        const uInputEl = (element as any).$el;
        return uInputEl?.querySelector("input") || uInputEl || null;
    }

    // For regular input element
    return element as HTMLInputElement;
});

// Methods
const updateCursorPosition = () => {
    nextTick(() => {
        const input = inputElement.value;
        if (input) {
            cursorPosition.value = input.selectionStart || 0;
        }
    });
};

const handleInput = (event: Event) => {
    const target = event.target as HTMLInputElement;
    cursorPosition.value = target.selectionStart || 0;

    // Only show suggestions automatically when search bar is empty
    if (!inputValue.value.trim()) {
        isAutocompleteIntentional.value = false; // Automatic suggestion
        autocomplete.showSuggestions(inputValue.value, cursorPosition.value);
    } else {
        // Hide suggestions when user is typing/pasting (they can use Ctrl+Space to show them)
        isAutocompleteIntentional.value = false;
        autocomplete.hideSuggestions();
    }
};

const handleKeyDown = (event: KeyboardEvent) => {
    // Handle Ctrl+Space to trigger autocomplete
    if (event.ctrlKey && event.key === " ") {
        event.preventDefault();
        triggerAutocomplete();
        return;
    }

    // Handle autocomplete navigation
    if (autocomplete.state.isVisible) {
        switch (event.key) {
            case "ArrowDown":
                event.preventDefault();
                autocomplete.navigateSuggestions("down");
                break;
            case "ArrowUp":
                event.preventDefault();
                autocomplete.navigateSuggestions("up");
                break;
            case "Enter":
                event.preventDefault();
                // Only apply suggestion if autocomplete was intentionally triggered or field is empty
                if (isAutocompleteIntentional.value || !inputValue.value.trim()) {
                    const selected = autocomplete.getSelectedSuggestion();
                    if (selected) {
                        applySuggestion(selected);
                    } else {
                        emit("enter");
                    }
                } else {
                    // User has text and autocomplete wasn't intentional - they want to search
                    autocomplete.hideSuggestions();
                    emit("enter");
                }
                break;
            case "Escape":
                event.preventDefault();
                autocomplete.hideSuggestions();
                break;
            case "Tab":
                // Allow tab to accept suggestion only if autocomplete was intentionally triggered or field is empty
                if (isAutocompleteIntentional.value || !inputValue.value.trim()) {
                    const tabSelected = autocomplete.getSelectedSuggestion();
                    if (tabSelected) {
                        event.preventDefault();
                        applySuggestion(tabSelected);
                    }
                }
                break;
        }
    } else {
        // Handle regular input events
        switch (event.key) {
            case "Enter":
                emit("enter");
                break;
        }
    }

    // Update cursor position after key events
    nextTick(() => {
        updateCursorPosition();
    });
};

const handleFocus = () => {
    emit("focus");
    showAutocompleteOnFocus.value = true;

    // Only show suggestions on focus if search bar is empty
    if (!inputValue.value.trim()) {
        isAutocompleteIntentional.value = false; // Automatic suggestion on focus
        nextTick(() => {
            autocomplete.showSuggestions(inputValue.value, cursorPosition.value);
        });
    }
};

const handleBlur = () => {
    emit("blur");
    showAutocompleteOnFocus.value = false;

    // Delay hiding suggestions to allow for clicking on suggestions
    setTimeout(() => {
        if (!showAutocompleteOnFocus.value) {
            autocomplete.hideSuggestions();
        }
    }, 150);
};

const handleClick = () => {
    updateCursorPosition();

    // Only show suggestions on click if search bar is empty
    if (!inputValue.value.trim()) {
        isAutocompleteIntentional.value = false; // Automatic suggestion on click
        autocomplete.showSuggestions(inputValue.value, cursorPosition.value);
    }
};

const triggerAutocomplete = () => {
    updateCursorPosition();
    isAutocompleteIntentional.value = true; // User intentionally triggered
    autocomplete.showSuggestions(inputValue.value, cursorPosition.value);
};

const handleSuggestionSelect = (suggestion: any) => {
    applySuggestion(suggestion);
};

const handleSuggestionHighlight = (index: number) => {
    if (index === -1) {
        autocomplete.hideSuggestions();
    } else {
        // Update selected index using the exposed method
        autocomplete.setSelectedIndex(index);
    }
};

const applySuggestion = (suggestion: any) => {
    const result = autocomplete.applySuggestion(inputValue.value, cursorPosition.value, suggestion);

    inputValue.value = result.newQuery;

    // Set cursor position after applying suggestion
    nextTick(() => {
        const input = inputElement.value;
        if (input) {
            input.focus();
            input.setSelectionRange(result.newCursorPosition, result.newCursorPosition);
            cursorPosition.value = result.newCursorPosition;
        }
    });

    autocomplete.hideSuggestions();
    isAutocompleteIntentional.value = false; // Reset flag after applying suggestion
};

// Initialize field names on mount
onMounted(() => {
    autocomplete.loadFieldNames();
});

// Expose methods for parent components
defineExpose({
    focus: () => inputElement.value?.focus(),
    blur: () => inputElement.value?.blur(),
    triggerAutocomplete,
});
</script>
