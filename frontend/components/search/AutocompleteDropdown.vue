<template>
    <Teleport to="body">
        <div
            v-if="suggestions.length > 0 && isVisible"
            ref="dropdownRef"
            class="fixed z-50 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto scroll-smooth"
            :style="dropdownStyle"
        >
            <div class="py-1">
                <div
                    v-for="(suggestion, index) in suggestions"
                    :key="suggestion.value"
                    :data-index="index"
                    class="px-3 py-2 cursor-pointer text-sm flex items-center gap-2 hover:bg-blue-50 transition-colors"
                    :class="{
                        'bg-blue-100 text-primary': index === selectedIndex,
                        'text-gray-900': index !== selectedIndex,
                    }"
                    @click="$emit('select', suggestion)"
                    @mouseenter="$emit('highlight', index)"
                >
                    <UIcon
                        :name="suggestion.type === 'field' ? 'i-heroicons-tag' : 'i-heroicons-code-bracket'"
                        class="w-4 h-4 flex-shrink-0"
                        :class="suggestion.type === 'field' ? 'text-primary' : 'text-eco'"
                    />
                    <span
                        class="font-mono flex-1 truncate min-w-0"
                        :class="suggestion.type === 'field' ? 'text-primary' : 'text-eco'"
                        :title="suggestion.value"
                        style="max-width: 200px"
                    >
                        {{ suggestion.value }}
                    </span>
                    <span
                        v-if="suggestion.type === 'operator' && suggestion.description"
                        class="text-xs text-gray-500 ml-auto"
                    >
                        {{ suggestion.description }}
                    </span>
                </div>
            </div>

            <!-- Footer with keyboard hints -->
            <div class="border-t border-primary-100 px-3 py-2 bg-gray-50 text-xs text-energy">
                <div class="flex items-center justify-between">
                    <span>
                        <kbd class="px-1 py-0.5 bg-white border border-gray-300 rounded text-xs">↑↓</kbd>
                        to navigate
                    </span>
                    <span>
                        <kbd class="px-1 py-0.5 bg-white border border-gray-300 rounded text-xs">Enter</kbd>
                        to select
                    </span>
                    <span>
                        <kbd class="px-1 py-0.5 bg-white border border-gray-300 rounded text-xs">Esc</kbd>
                        to close
                    </span>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<script setup lang="ts">
interface SuggestionItem {
    readonly value: string;
    readonly type: "field" | "operator" | "value";
    readonly description?: string;
}

interface Props {
    suggestions: readonly SuggestionItem[];
    isVisible: boolean;
    selectedIndex: number;
    inputElement: HTMLElement | null;
    cursorPosition: number;
}

interface Emits {
    (e: "select", suggestion: SuggestionItem): void;
    (e: "highlight", index: number): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// Refs
const dropdownRef = ref<HTMLElement | null>(null);

// Computed styles for positioning
const dropdownStyle = computed(() => {
    if (!props.inputElement) {
        return { display: "none" };
    }

    const inputRect = props.inputElement.getBoundingClientRect();
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

    // Position dropdown below the input
    const top = inputRect.bottom + scrollTop + 4;
    const left = inputRect.left + scrollLeft;
    const maxWidth = inputRect.width;

    return {
        top: `${top}px`,
        left: `${left}px`,
        minWidth: `${Math.min(maxWidth, 300)}px`,
        maxWidth: `${Math.max(maxWidth, 400)}px`,
    };
});

// Methods
const scrollToSelectedItem = () => {
    if (!dropdownRef.value || props.selectedIndex < 0) return;

    const selectedElement = dropdownRef.value.querySelector(`[data-index="${props.selectedIndex}"]`) as HTMLElement;
    const scrollContainer = dropdownRef.value;

    if (selectedElement && scrollContainer) {
        const containerRect = scrollContainer.getBoundingClientRect();
        const itemRect = selectedElement.getBoundingClientRect();

        // Check if item is outside the visible area
        const isAbove = itemRect.top < containerRect.top;
        const isBelow = itemRect.bottom > containerRect.bottom;

        if (isAbove || isBelow) {
            selectedElement.scrollIntoView({
                behavior: "smooth",
                block: "nearest",
            });
        }
    }
};

// Handle clicks outside to close dropdown
const handleClickOutside = (event: MouseEvent) => {
    if (
        props.isVisible &&
        dropdownRef.value &&
        !dropdownRef.value.contains(event.target as Node) &&
        props.inputElement &&
        !props.inputElement.contains(event.target as Node)
    ) {
        // Emit a close event instead of handling it here
        emit("highlight", -1);
    }
};

// Watchers
watch(
    () => props.selectedIndex,
    () => {
        if (props.isVisible && props.selectedIndex >= 0) {
            nextTick(() => {
                scrollToSelectedItem();
            });
        }
    },
);

// Lifecycle
onMounted(() => {
    document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
    document.removeEventListener("click", handleClickOutside);
});
</script>

<style scoped>
.truncate {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
</style>
