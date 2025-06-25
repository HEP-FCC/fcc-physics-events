<script setup lang="ts">
import { ref, reactive } from "vue";
import { getApiClient } from "~/composables/getApiClient";
import type { Sample } from "~/types/sample";

// State management
const searchQuery = ref("");
const isLoading = ref(false);
const samples = ref<Sample[]>([]);
const error = ref<string | null>(null);
const apiClient = getApiClient();

// Search for samples
async function searchSamples() {
  if (!searchQuery.value.trim()) {
    return;
  }

  isLoading.value = true;
  error.value = null;

  try {
    const response = await apiClient.searchSamples(searchQuery.value);
    samples.value = response?.samples || [];
  } catch (err: any) {
    error.value = err.message || "Failed to search samples";
    samples.value = []; // Ensure samples is always an array
  } finally {
    isLoading.value = false;
  }
}

// Toggle metadata visibility (if needed - although requirement is to always show)
const expandedRows = reactive(new Set<number>());

function toggleMetadata(sampleId: number) {
  if (expandedRows.has(sampleId)) {
    expandedRows.delete(sampleId);
  } else {
    expandedRows.add(sampleId);
  }
}
</script>

<template>
  <div class="container-lg py-8">
    <h1 class="text-2xl font-bold mb-6">FCC Physics Events Sample Search</h1>

    <!-- Search Form -->
    <div class="mb-6 flex gap-2">
      <UInput
        v-model="searchQuery"
        placeholder="Enter your search query..."
        class="flex-1"
        @keyup.enter="searchSamples"
      />
      <UButton label="Search" color="primary" :loading="isLoading" @click="searchSamples" />
    </div>

    <!-- Error Message -->
    <UAlert v-if="error" color="red" variant="soft" icon="i-lucide-alert-triangle" class="mb-4" :title="error" />

    <!-- Results -->
    <div v-if="samples && samples.length > 0" class="bg-white rounded-lg shadow">
      <!-- Sample List -->
      <div v-for="sample in samples" :key="sample?.id || Math.random()" class="border-b last:border-0">
        <!-- Main Sample Row -->
        <div class="p-4 bg-gray-50">
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <h3 class="font-medium">{{ sample?.name || "Unnamed Sample" }}</h3>
              <h3 class="font-medium">{{ sample?.accelerator_type || "Unnamed Sample" }}</h3>
              <h3 class="font-medium">{{ sample?.detector || "Unnamed Sample" }}</h3>
              <div class="flex flex-wrap gap-2 mt-1">
                <UBadge v-if="sample?.detector" color="blue" variant="subtle">{{ sample.detector }}</UBadge>
                <UBadge v-if="sample?.framework" color="green" variant="subtle">{{ sample.framework }}</UBadge>
                <UBadge v-if="sample?.campaign" color="amber" variant="subtle">{{ sample.campaign }}</UBadge>
                <UBadge v-if="sample?.accelerator_type" color="purple" variant="subtle">{{
                  sample.accelerator_type
                }}</UBadge>
              </div>
            </div>
            <UButton
              icon="i-lucide-info"
              color="gray"
              variant="ghost"
              :aria-label="`More details for sample ${sample?.id || 'unknown'}`"
              @click="sample?.id && toggleMetadata(sample.id)"
            />
          </div>
        </div>

        <!-- Metadata Section - Always visible as per requirement -->
        <div class="p-4 bg-gray-100 text-sm">
          <div v-if="sample?.metadata" class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div v-for="(value, key) in sample.metadata" :key="key" class="flex">
              <span class="font-medium mr-2">{{ key }}:</span>
              <span>{{ value }}</span>
            </div>
          </div>
          <div v-else class="text-gray-500">No metadata available</div>
        </div>
      </div>
    </div>

    <!-- Empty Search Results -->
    <div
      v-else-if="samples && samples.length === 0 && !isLoading"
      class="p-8 text-center text-gray-500 bg-white rounded-lg shadow"
    >
      No samples found matching your query
    </div>
  </div>
</template>

<style scoped>
.metadata-enter-active,
.metadata-leave-active {
  transition: max-height 0.3s ease, opacity 0.3s ease;
}

.metadata-enter-from,
.metadata-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>
