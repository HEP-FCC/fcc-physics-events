<script setup lang="ts">
const props = defineProps<{
    initialFilters: Record<string, string>;
}>();
</script>

<template>
    <UContainer class="py-4 sm:py-6 lg:py-8">
        <DatasetSearchInterface :initial-filters="props.initialFilters" />
    </UContainer>
</template>
