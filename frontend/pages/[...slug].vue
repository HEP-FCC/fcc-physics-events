<template>
    <div>
        <HelloWorld :initial-filters="filters" />
    </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();

const filters = computed(() => {
    const params = route.params.slug || [];
    const filters: Record<string, string> = {};

    // Map URL segments to filter fields
    if (params.length > 0 && params[0]) {
        filters.framework_name = params[0];
    }
    if (params.length > 1 && params[1]) {
        filters.campaign_name = params[1];
    }
    if (params.length > 2 && params[2]) {
        filters.detector = params[2];
    }

    return filters;
});

// Set page title based on active filters
const pageTitle = computed(() => {
    const filterNames = [];
    if (filters.value.framework_name) filterNames.push(filters.value.framework_name);
    if (filters.value.campaign_name) filterNames.push(filters.value.campaign_name);
    if (filters.value.detector) filterNames.push(filters.value.detector);

    if (filterNames.length > 0) {
        return `FCC Physics Events - ${filterNames.join(" / ")}`;
    }
    return "FCC Physics Events Search";
});

// Set the page title and meta
useHead({
    title: pageTitle,
    meta: [
        {
            name: "description",
            content: computed(() => {
                if (Object.keys(filters.value).length > 0) {
                    const filterDesc = Object.entries(filters.value)
                        .map(([key, value]) => `${key.replace("_", " ")}: ${value}`)
                        .join(", ");
                    return `Search FCC physics events filtered by ${filterDesc}`;
                }
                return "Search and explore FCC physics simulation events and data";
            }),
        },
    ],
});
</script>
