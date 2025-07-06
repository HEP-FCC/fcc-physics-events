<template>
    <UContainer class="py-4 sm:py-6 lg:py-8">
        <DatasetSearchInterface :initial-filters="activeFilters" />
    </UContainer>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useNavigationConfig } from "../composables/useNavigationConfig";

const route = useRoute();
const { parseRouteParams, generatePageTitle, generatePageDescription } = useNavigationConfig();

const activeFilters = computed(() => {
    const params = Array.isArray(route.params.slug) ? route.params.slug : [];
    return parseRouteParams(params);
});

// Set page title based on active filters
const pageTitle = computed(() => generatePageTitle(activeFilters.value));

// Set the page title and meta
useHead({
    title: pageTitle,
    meta: [
        {
            name: "description",
            content: computed(() => generatePageDescription(activeFilters.value)),
        },
    ],
});
</script>
