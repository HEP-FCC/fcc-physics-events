<template>
    <div>
        <HelloWorld :initial-filters="filters" />
    </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useNavigationConfig } from "../composables/useNavigationConfig";

const route = useRoute();
const { parseRouteParams, generatePageTitle, generatePageDescription } = useNavigationConfig();

const filters = computed(() => {
    const params = Array.isArray(route.params.slug) ? route.params.slug : [];
    return parseRouteParams(params);
});

// Set page title based on active filters
const pageTitle = computed(() => generatePageTitle(filters.value));

// Set the page title and meta
useHead({
    title: pageTitle,
    meta: [
        {
            name: "description",
            content: computed(() => generatePageDescription(filters.value)),
        },
    ],
});
</script>
