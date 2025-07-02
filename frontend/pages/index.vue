<template>
    <div>
        <HelloWorld :initial-filters="{}" />
    </div>
</template>

<script setup lang="ts">
// Set page title and meta for the main page
useHead({
    title: "FCC Physics Datasets Search",
    meta: [
        {
            name: "description",
            content:
                "Search and explore FCC physics simulation datasets and data across different stages, campaigns, and detectors",
        },
    ],
});
</script>
