<template>
    <div class="debug-panel bg-gray-100 p-4 m-4 rounded-lg text-sm">
        <h3 class="font-bold mb-2">Navigation Debug Panel</h3>

        <div class="mb-2"><strong>Navigation Ready:</strong> {{ isNavigationReady() }}</div>

        <div class="mb-2"><strong>Navigation Order:</strong> {{ navigationOrder.join(", ") || "None" }}</div>

        <div class="mb-4">
            <button @click="triggerPreload" class="bg-blue-500 text-white px-3 py-1 rounded text-xs hover:bg-blue-600">
                Trigger Manual Preload
            </button>
        </div>

        <div class="space-y-2">
            <div v-for="type in navigationOrder" :key="type" class="border-l-2 border-blue-300 pl-2">
                <div class="font-medium">{{ type }}</div>
                <div class="text-xs text-gray-600">
                    Items: {{ getItems(type).length }} | Loading: {{ isLoading(type) }} | Open: {{ isOpen(type) }}
                </div>
                <div v-if="getItems(type).length > 0" class="text-xs text-green-600">
                    ✓ Data loaded:
                    {{
                        getItems(type)
                            .slice(0, 3)
                            .map((item) => item.name)
                            .join(", ")
                    }}
                    <span v-if="getItems(type).length > 3">... ({{ getItems(type).length - 3 }} more)</span>
                </div>
                <div v-else class="text-xs text-red-600">✗ No data loaded</div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { useNavigationState } from "~/composables/useNavigationState";
import { useNavigationConfig } from "~/composables/useNavigationConfig";

const { navigationOrder, getItems, isLoading, isOpen, proactivelyLoadDropdownData } = useNavigationState();

const { isNavigationReady } = useNavigationConfig();

const triggerPreload = async () => {
    console.log("Manually triggering preload...");
    await proactivelyLoadDropdownData();
};
</script>
