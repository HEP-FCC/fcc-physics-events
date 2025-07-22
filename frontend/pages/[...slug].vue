<template>
    <UContainer class="py-4 sm:py-6 lg:py-8">
        <DatasetSearchInterface :initial-filters="activeFilters" :route-params="routeParams" />
    </UContainer>
</template>

<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";
import { useRoute } from "vue-router";
import { useDynamicNavigation } from "~/composables/useDynamicNavigation";

const route = useRoute();
const { parseRouteToFilters, parseRouteToPath, getPageTitle } = useDynamicNavigation();

const routeParams = computed(() => {
    return Array.isArray(route.params.slug) ? route.params.slug : route.params.slug ? [route.params.slug] : [];
});

// Use refs for async data
const activeFilters = ref<Record<string, string>>({});
const currentPath = ref<Record<string, string | null>>({});

// Watch route params and update data asynchronously
watchEffect(() => {
    const params = routeParams.value;
    try {
        activeFilters.value = parseRouteToFilters(params);
        currentPath.value = parseRouteToPath(params);
    } catch (error) {
        console.error("Error parsing route:", error);
        activeFilters.value = {};
        currentPath.value = {};
    }
});

// Set the page title and meta
useHead({
    title: () => {
        const path = currentPath.value;
        try {
            return Object.keys(path).some((key) => path[key]) ? getPageTitle(path) : "FCC Physics Datasets Search";
        } catch (error) {
            console.error("Error getting page title:", error);
            return "FCC Physics Datasets Search";
        }
    },
    meta: [
        {
            name: "description",
            content: () => {
                const filters = activeFilters.value;
                if (Object.keys(filters).length > 0) {
                    const filterDesc = Object.entries(filters)
                        .map(([key, value]) => `${key.replace("_", " ")}: ${value}`)
                        .join(", ");
                    return `Search FCC physics datasets filtered by ${filterDesc}`;
                }
                return "Search and explore FCC physics simulation datasets and data";
            },
        },
    ],
});
</script>
