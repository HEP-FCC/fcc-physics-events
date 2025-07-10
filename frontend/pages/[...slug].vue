<template>
    <UContainer class="py-4 sm:py-6 lg:py-8">
        <MegaDatasetInterface :initial-filters="activeFilters" :route-params="routeParams" />
    </UContainer>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();

// Parse route parameters into filters for API queries
function parseRouteParams(params: string[]): Record<string, string> {
    const filters: Record<string, string> = {};
    const dropdownKeys = ["stage", "campaign", "detector"];

    dropdownKeys.forEach((type, index) => {
        if (params.length > index && params[index]) {
            filters[`${type}_name`] = params[index];
        }
    });

    return filters;
}

// Generate page title from active filters
function generatePageTitle(filters: Record<string, string>): string {
    const filterNames = ["stage", "campaign", "detector"].map((type) => filters[`${type}_name`]).filter(Boolean);

    if (filterNames.length > 0) {
        return `FCC Physics Datasets - ${filterNames.join(" / ")}`;
    }
    return "FCC Physics Datasets Search";
}

// Generate page description from active filters
function generatePageDescription(filters: Record<string, string>): string {
    if (Object.keys(filters).length > 0) {
        const filterDesc = Object.entries(filters)
            .map(([key, value]) => `${key.replace("_", " ")}: ${value}`)
            .join(", ");
        return `Search FCC physics datasets filtered by ${filterDesc}`;
    }
    return "Search and explore FCC physics simulation datasets and data";
}

const activeFilters = computed(() => {
    const params = Array.isArray(route.params.slug) ? route.params.slug : route.params.slug ? [route.params.slug] : [];
    return parseRouteParams(params);
});

const routeParams = computed(() => {
    return Array.isArray(route.params.slug) ? route.params.slug : route.params.slug ? [route.params.slug] : [];
});

// Set the page title and meta
useHead({
    title: () => generatePageTitle(activeFilters.value),
    meta: [
        {
            name: "description",
            content: computed(() => generatePageDescription(activeFilters.value)),
        },
    ],
});
</script>
