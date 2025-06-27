<script setup lang="ts">
import { ref, reactive, computed, watch } from "vue";
import { getApiClient } from "~/composables/getApiClient";
import type { Sample, PaginatedResponse } from "~/types/sample";
import { watchDebounced } from "@vueuse/core";

// --- State ---
const searchQuery = ref("");
const isLoading = ref(false);
const samples = ref<Sample[]>([]);
const error = ref<string | null>(null);
const apiClient = getApiClient();
const page = ref(1);
const pageSize = ref(20);
const totalSamples = ref(0);

// --- Core Fetch Logic ---
// This function now reads from the component's state instead of taking arguments.
const performSearch = async () => {
  if (!searchQuery.value.trim()) {
    samples.value = [];
    totalSamples.value = 0;
    return;
  }

  isLoading.value = true;
  error.value = null;

  try {
    const offset = (page.value - 1) * pageSize.value;
    const response: PaginatedResponse = await apiClient.searchSamples(searchQuery.value, pageSize.value, offset);
    samples.value = response.items || [];
    totalSamples.value = response.total || 0;
  } catch (err: any) {
    error.value = err.message || "Failed to fetch samples.";
    samples.value = [];
    totalSamples.value = 0;
  } finally {
    isLoading.value = false;
  }
};

// --- Watchers for Reactivity ---

// This watcher triggers a new search whenever `currentPage` changes.
// This is the key fix for making pagination clicks work.
watch(page, () => {
  performSearch();
});

// This watcher triggers when the user types in the search box.
// It resets the page to 1, which in turn triggers the `currentPage` watcher above.
watchDebounced(
  searchQuery,
  () => {
    // If we are already on page 1, the watcher won't fire, so we must trigger manually.
    // Otherwise, changing the page to 1 will trigger the other watcher.
    if (page.value === 1) {
      performSearch();
    } else {
      page.value = 1;
    }
  },
  { debounce: 500, maxWait: 2000 },
);

// --- UI Interaction ---
const expandedRows = reactive(new Set<number>());
function toggleMetadata(processId: number) {
  if (expandedRows.has(processId)) {
    expandedRows.delete(processId);
  } else {
    expandedRows.add(processId);
  }
}
</script>

<template>
  <div class="container mx-auto p-4 sm:p-6 lg:p-8">
    <h1 class="text-3xl font-bold mb-6 text-gray-800">FCC Physics Events Sample Search</h1>

    <div class="mb-6">
      <UInput
        v-model="searchQuery"
        placeholder='e.g., detector:"IDEA" AND metadata.status="done"'
        class="w-full"
        size="lg"
        icon="i-heroicons-magnifying-glass"
      />
    </div>

    <UAlert
      v-if="error"
      color="red"
      variant="soft"
      icon="i-heroicons-exclamation-triangle"
      class="mb-4"
      :title="error"
      description="Please check your query syntax and try again."
      closable
      @close="error = null"
    />

    <div v-if="isLoading" class="space-y-4">
      <USkeleton v-for="i in 5" :key="i" class="h-12 w-full" />
    </div>

    <div v-else-if="samples.length > 0">
      <UPagination v-model:page="page" :total="totalSamples" :items-per-page="pageSize" />
      <div class="overflow-hidden rounded-lg shadow-md border border-gray-200">
        <div v-for="sample in samples" :key="sample.process_id" class="border-b last:border-0 border-gray-200">
          <div class="p-4 bg-white hover:bg-gray-50 transition-colors duration-200">
            <div class="flex items-center justify-between">
              <div class="flex-1 min-w-0">
                <p class="font-semibold text-lg text-gray-900 truncate">{{ sample.name }}</p>
                <div class="flex flex-wrap gap-2 mt-2">
                  <UBadge v-if="sample.detector_name" color="blue" variant="subtle"
                    >Detector: {{ sample.detector_name }}</UBadge
                  >
                  <UBadge v-if="sample.framework_name" color="green" variant="subtle"
                    >Framework: {{ sample.framework_name }}</UBadge
                  >
                  <UBadge v-if="sample.campaign_name" color="amber" variant="subtle"
                    >Campaign: {{ sample.campaign_name }}</UBadge
                  >
                  <UBadge v-if="sample.accelerator_name" color="purple" variant="subtle"
                    >Accelerator: {{ sample.accelerator_name }}</UBadge
                  >
                </div>
              </div>
              <UButton
                :icon="expandedRows.has(sample.process_id) ? 'i-heroicons-chevron-up' : 'i-heroicons-chevron-down'"
                color="gray"
                variant="ghost"
                :aria-label="`Details for ${sample.name}`"
                @click="toggleMetadata(sample.process_id)"
              />
            </div>
          </div>
          <div v-if="expandedRows.has(sample.process_id)" class="p-4 bg-gray-50 text-sm border-t border-gray-200">
            <h4 class="font-bold text-md mb-2 text-gray-700">Metadata</h4>
            <pre
              class="bg-gray-100 p-2 rounded text-xs whitespace-pre-wrap break-all"
            ><code>{{ JSON.stringify(sample.metadata, null, 2) }}</code></pre>
          </div>
        </div>
      </div>
      <div class="flex justify-between items-center mt-4 text-sm text-gray-600">
        <div>
          Showing
          <strong>{{ (page - 1) * pageSize + 1 }}-{{ Math.min(page * pageSize, totalSamples) }}</strong>
          of <strong>{{ totalSamples }}</strong> results
        </div>
        <!--
          Using v-model now correctly binds the page number. The `watch` effect
          handles the logic of fetching new data when this value changes.
        -->
        <UPagination v-model:page="page" :total="totalSamples" :items-per-page="pageSize" />
      </div>
    </div>

    <div v-else class="p-8 text-center text-gray-500 bg-white rounded-lg shadow-sm border border-dashed">
      <p>No samples found.</p>
      <p class="text-sm">Enter a query to begin searching.</p>
    </div>
  </div>
</template>
