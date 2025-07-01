<template>
    <div>
        <HelloWorld :initial-filters="{}" />
    </div>
</template>

<script setup lang="ts">
// Set page title and meta for the main page
useHead({
    title: "FCC Physics Events Search",
    meta: [
        {
            name: "description",
            content:
                "Search and explore FCC physics simulation events and data across different frameworks, campaigns, and detectors",
        },
    ],
});
</script>
