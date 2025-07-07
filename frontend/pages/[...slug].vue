<template>
    <UContainer class="py-4 sm:py-6 lg:py-8">
        <DatasetSearchInterface :initial-filters="activeFilters" :route-params="routeParams" />
    </UContainer>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import { navigationConfig } from "../composables/navigationConfig";

const route = useRoute();
const { parseRouteParams, generatePageTitle, generatePageDescription } = navigationConfig();

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
