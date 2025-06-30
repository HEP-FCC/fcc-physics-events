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

  if (params.length > 0) {
    filters.framework_name = params[0];
  }
  if (params.length > 1) {
    filters.campaign_name = params[1];
  }
  if (params.length > 2) {
    filters.detector = params[2];
  }

  return filters;
});
</script>