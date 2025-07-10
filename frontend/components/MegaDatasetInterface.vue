<template>
    <div class="space-y-6">
        <UCard>
            <template #header>
                <h1 class="text-3xl font-bold">FCC Physics Datasets Search</h1>
            </template>

            <!-- Navigation Menu -->
            <div class="bg-white border-b border-gray-200 mb-6">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <nav class="flex space-x-8 py-4">
                        <div v-for="(dropdown, type) in activeDropdowns" :key="type" class="relative">
                            <UButton
                                :color="currentPath[type as DropdownType] ? 'primary' : 'neutral'"
                                :variant="currentPath[type as DropdownType] ? 'solid' : 'ghost'"
                                trailing-icon="i-heroicons-chevron-down-20-solid"
                                :loading="dropdown.isLoading"
                                @click="toggleDropdown(type as DropdownType)"
                            >
                                <UIcon :name="dropdown.icon" class="mr-2" />
                                {{ currentPath[type as DropdownType] || dropdown.label }}
                            </UButton>

                            <div
                                v-if="dropdown.isOpen"
                                class="absolute top-full left-0 mt-1 w-auto min-w-48 max-w-xs bg-white border border-gray-200 rounded-md shadow-lg z-50"
                            >
                                <div class="p-2">
                                    <div v-if="currentPath[type as DropdownType]" class="mb-2">
                                        <button
                                            class="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-gray-50 rounded flex items-center whitespace-nowrap"
                                            @click="
                                                clearSelectionPath(type as DropdownType);
                                                dropdown.isOpen = false;
                                            "
                                        >
                                            <UIcon name="i-heroicons-x-mark" class="mr-2" />
                                            {{ dropdown.clearLabel }}
                                        </button>
                                    </div>

                                    <div v-if="dropdown.isLoading" class="p-2">
                                        <USkeleton class="h-4 w-24" />
                                    </div>

                                    <div v-else class="space-y-1">
                                        <button
                                            v-for="item in dropdown.items"
                                            :key="item.id"
                                            class="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 rounded whitespace-nowrap"
                                            :class="{
                                                'bg-primary-50 text-primary-700':
                                                    currentPath[type as DropdownType] === item.name,
                                            }"
                                            @click="
                                                navigateToPath(type as DropdownType, item.name);
                                                dropdown.isOpen = false;
                                            "
                                        >
                                            {{ item.name }}
                                        </button>
                                        <div v-if="!dropdown.items.length" class="px-3 py-2 text-sm text-gray-500">
                                            No options available.
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="flex items-center space-x-2 text-sm text-gray-500 ml-auto">
                            <span v-if="!Object.values(currentPath).some((v) => v)"> All Datasets </span>
                            <template v-else>
                                <span>Filtered by:</span>
                                <template v-for="(dropdown, type) in activeDropdowns" :key="type">
                                    <UBadge
                                        v-if="currentPath[type as DropdownType]"
                                        :color="getBadgeColor(type as DropdownType)"
                                        variant="soft"
                                    >
                                        {{ dropdown.label }}: {{ currentPath[type as DropdownType] }}
                                    </UBadge>
                                </template>
                            </template>
                        </div>
                    </nav>
                </div>
            </div>

            <!-- Search Controls -->
            <div class="space-y-2">
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Search Query
                    <span v-if="showFilterNote" class="text-xs text-gray-600 dark:text-gray-400 ml-1">
                        (Additional filters from navigation applied automatically)
                    </span>
                </label>
                <div class="flex gap-2 items-center">
                    <div class="flex-grow relative">
                        <UInput
                            v-model="userSearchQuery"
                            :placeholder="searchPlaceholderText"
                            size="lg"
                            icon="i-heroicons-magnifying-glass"
                            class="pr-10 w-full"
                            @keydown.enter="handleSearch"
                        />
                        <UTooltip
                            class="absolute right-2 top-1/2 transform -translate-y-1/2 z-10"
                            :content="{ side: 'top', sideOffset: 8 }"
                        >
                            <template #content>
                                <div
                                    class="max-w-md p-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg"
                                >
                                    <div class="font-semibold text-sm mb-3 text-gray-900 dark:text-gray-100">
                                        Query Language Help
                                    </div>
                                    <div class="text-xs text-gray-700 dark:text-gray-300 space-y-3">
                                        <div>
                                            <div class="font-medium mb-2 text-gray-800 dark:text-gray-200">
                                                Example search queries:
                                            </div>
                                            <div class="space-y-1.5">
                                                <div>
                                                    <code :class="codeClass">"H to cu"</code>
                                                    - Filter by any field containing this string
                                                </div>
                                                <div>
                                                    <code :class="codeClass"
                                                        >metadata.description:"ee -> Z(nu nu)"</code
                                                    >
                                                    - Metadata text field
                                                </div>
                                                <div>
                                                    <code :class="codeClass">metadata.sum-of-weights>100000</code>
                                                    - Metadata number filter
                                                </div>
                                            </div>
                                        </div>
                                        <div>
                                            <div class="font-medium mb-2 text-gray-800 dark:text-gray-200">
                                                Boolean Operators:
                                            </div>
                                            <div class="flex flex-wrap gap-1">
                                                <code :class="codeClass">AND</code>
                                                <code :class="codeClass">OR</code>
                                                <code :class="codeClass">NOT</code>
                                            </div>
                                        </div>
                                        <div>
                                            <div class="font-medium mb-2 text-gray-800 dark:text-gray-200">
                                                Comparison Operators:
                                            </div>
                                            <div class="flex flex-wrap gap-1">
                                                <code :class="codeClass">=</code>
                                                <code :class="codeClass">!=</code>
                                                <code :class="codeClass">></code>
                                                <code :class="codeClass"><</code>
                                                <code :class="codeClass">>=</code>
                                                <code :class="codeClass"><=</code>
                                            </div>
                                            <div class="text-xs text-gray-600 dark:text-gray-400 mt-2">
                                                <div>
                                                    <code :class="codeClass">:</code>
                                                    substring,
                                                    <code :class="codeClass">=~</code>
                                                    regex match,
                                                    <code :class="codeClass">!~</code>
                                                    regex not match,
                                                    <code :class="codeClass">:*</code>
                                                    field exists
                                                </div>
                                            </div>
                                        </div>
                                        <div class="pt-2 border-t border-gray-200 dark:border-gray-600 text-center">
                                            <a
                                                href="https://cloud.google.com/logging/docs/view/logging-query-language"
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                class="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 cursor-pointer hover:underline text-xs font-medium transition-colors inline-flex items-center gap-1"
                                            >
                                                View Full Documentation
                                                <svg
                                                    class="w-3 h-3"
                                                    fill="none"
                                                    stroke="currentColor"
                                                    viewBox="0 0 24 24"
                                                >
                                                    <path
                                                        stroke-linecap="round"
                                                        stroke-linejoin="round"
                                                        stroke-width="2"
                                                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                                                    />
                                                </svg>
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </template>
                            <UButton
                                icon="i-heroicons-information-circle"
                                color="neutral"
                                variant="ghost"
                                size="xs"
                                :padded="false"
                                class="w-5 h-6 hover:bg-gray-100 dark:hover:bg-gray-800"
                                @click="openQueryDocumentation"
                            />
                        </UTooltip>
                    </div>
                    <UButton
                        icon="i-heroicons-magnifying-glass"
                        color="primary"
                        variant="solid"
                        size="lg"
                        class="cursor-pointer"
                        @click="handleSearch"
                    >
                        Search
                    </UButton>
                    <div class="relative">
                        <UTooltip text="Copy link" placement="top" class="cursor-pointer">
                            <template #default>
                                <UButton
                                    icon="i-heroicons-link"
                                    color="neutral"
                                    variant="outline"
                                    size="lg"
                                    :loading="isPermalinkCopyInProgress"
                                    :disabled="!canCopyLink"
                                    @click="handleCopyPermalink"
                                />
                            </template>
                        </UTooltip>
                        <div
                            v-if="showLinkCopiedFeedback"
                            class="absolute -top-10 left-1/2 transform -translate-x-1/2 bg-green-600 text-white text-xs px-2 py-1 rounded shadow-lg whitespace-nowrap z-10"
                        >
                            Link copied!
                        </div>
                    </div>
                </div>

                <UAlert
                    v-if="searchState.error"
                    color="error"
                    variant="soft"
                    icon="i-heroicons-exclamation-triangle"
                    :title="searchState.error"
                    description="Please check your query syntax and try again."
                    closable
                    @close="searchState.error = null"
                />

                <UAlert
                    v-if="!apiAvailable"
                    color="warning"
                    variant="soft"
                    icon="i-heroicons-exclamation-triangle"
                    title="API Server Unavailable"
                    description="Unable to connect to the backend server. Please check if the server is running."
                />
            </div>
        </UCard>

        <!-- Loading Skeleton -->
        <UCard v-if="showLoadingSkeleton">
            <div class="space-y-4">
                <USkeleton v-for="i in 5" :key="i" class="h-12 w-full" />
            </div>
        </UCard>

        <!-- Results -->
        <div v-else-if="searchState.datasets.length > 0" class="space-y-6">
            <!-- Dataset Controls & Results Summary -->
            <div
                class="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800"
            >
                <!-- Dataset Controls -->
                <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
                    <!-- Selection controls -->
                    <div class="flex items-center gap-2">
                        <UCheckbox
                            :model-value="allDatasetsSelected"
                            :disabled="searchState.datasets.length === 0"
                            @change="toggleSelectAll"
                        />
                        <label class="text-sm font-medium cursor-pointer" @click="toggleSelectAll">Select All</label>
                    </div>

                    <UButton
                        icon="i-heroicons-arrow-down-tray"
                        color="primary"
                        variant="solid"
                        size="sm"
                        :disabled="selectedCount === 0"
                        :loading="selectionState.isDownloading"
                        @click="downloadSelectedDatasets"
                    >
                        Download ({{ selectedCount }})
                    </UButton>

                    <div class="h-6 w-px bg-gray-300 dark:bg-gray-600" />

                    <UButton
                        :icon="allMetadataExpanded ? 'i-heroicons-eye-slash' : 'i-heroicons-eye'"
                        color="neutral"
                        variant="outline"
                        size="sm"
                        @click="toggleAllMetadata"
                    >
                        {{ allMetadataExpanded ? "Hide All" : "Show All" }}
                    </UButton>

                    <div class="h-6 w-px bg-gray-300 dark:bg-gray-600" />

                    <!-- Sorting controls -->
                    <div class="flex items-center gap-2">
                        <span class="text-sm font-medium text-gray-700 dark:text-gray-300">Sort by:</span>
                        <USelectMenu
                            :model-value="sortState.sortBy"
                            :items="sortingFieldOptions"
                            :loading="sortState.isLoading"
                            placeholder="Select field"
                            value-key="value"
                            :search-input="{ placeholder: 'Search fields...' }"
                            size="sm"
                            class="w-48"
                            @update:model-value="sortState.sortBy = $event"
                        />
                        <UButton
                            :icon="
                                sortState.sortOrder === 'asc'
                                    ? 'i-heroicons-bars-arrow-up'
                                    : 'i-heroicons-bars-arrow-down'
                            "
                            color="neutral"
                            variant="outline"
                            size="sm"
                            @click="toggleSortOrder"
                        />
                    </div>

                    <UButton
                        :icon="infiniteScrollEnabled ? 'i-heroicons-document-duplicate' : 'i-heroicons-arrows-up-down'"
                        color="neutral"
                        variant="outline"
                        size="sm"
                        @click="toggleMode"
                    >
                        {{ infiniteScrollEnabled ? "Pagination" : "Infinite Scroll" }}
                    </UButton>
                </div>

                <!-- Results Summary -->
                <div class="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
                    <!-- Left side: Results count and page size control -->
                    <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
                        <!-- Results count -->
                        <div class="text-sm text-gray-600 dark:text-gray-300">
                            Showing
                            <strong class="text-gray-900 dark:text-white">
                                {{ currentDisplayRange.start }}-{{ currentDisplayRange.end }}
                            </strong>
                            of
                            <strong class="text-gray-900 dark:text-white">
                                {{ currentDisplayRange.total }}
                            </strong>
                        </div>

                        <div class="h-6 w-px bg-gray-300 dark:bg-gray-600" />

                        <!-- Page size control -->
                        <div class="flex items-center gap-1 text-sm">
                            <UTooltip text="Allowed range: 20-1000" placement="top">
                                <span>Per page:</span>
                            </UTooltip>
                            <UInput
                                :model-value="pagination.pageSize"
                                type="number"
                                min="1"
                                max="100"
                                size="xs"
                                class="w-16"
                                @update:model-value="pagination.pageSize = Number($event)"
                                @change="handlePageSizeChange"
                            />
                        </div>
                    </div>
                </div>
            </div>

            <!-- Dataset List -->
            <div class="space-y-2">
                <!-- Dataset cards -->
                <UCard
                    v-for="(dataset, index) in searchState.datasets"
                    :key="dataset.dataset_id"
                    :data-dataset-card="index"
                    class="overflow-hidden select-text cursor-pointer"
                    @click="handleRowClick($event, dataset.dataset_id)"
                >
                    <div class="px-4 py-1">
                        <div class="flex items-center justify-between gap-4">
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center">
                                    <div class="flex-shrink-0 pr-4">
                                        <UCheckbox
                                            :model-value="isDatasetSelected(dataset.dataset_id)"
                                            @click.stop="toggleDatasetSelection(dataset.dataset_id)"
                                        />
                                    </div>

                                    <div class="w-88 flex-shrink-0">
                                        <h3 class="font-semibold text-base text-gray-900 dark:text-white">
                                            {{ dataset.name }}
                                        </h3>
                                    </div>

                                    <div
                                        v-for="badge in getBadgeItems(dataset)"
                                        :key="badge.key"
                                        :class="badge.widthClass"
                                        class="flex-shrink-0"
                                    >
                                        <UBadge v-if="badge.value" :color="badge.color" variant="subtle" size="md">
                                            <span>{{ badge.label }}:</span>
                                            <span class="ml-1">{{ badge.value }}</span>
                                        </UBadge>
                                    </div>
                                </div>
                            </div>

                            <UButton
                                :icon="
                                    isMetadataExpanded(dataset.dataset_id)
                                        ? 'i-heroicons-chevron-up'
                                        : 'i-heroicons-chevron-down'
                                "
                                color="primary"
                                variant="ghost"
                                size="md"
                                @click.stop="toggleMetadata(dataset.dataset_id)"
                            />
                        </div>
                    </div>

                    <!-- Metadata component (inline) -->
                    <div
                        v-if="isMetadataExpanded(dataset.dataset_id)"
                        class="border-t border-gray-200 bg-gray-50 cursor-default"
                        @click.stop
                    >
                        <div class="p-4">
                            <div v-if="metadataEditState[dataset.dataset_id]?.isEditing" class="space-y-3">
                                <textarea
                                    v-model="metadataEditState[dataset.dataset_id].json"
                                    :rows="getTextareaRows(dataset.dataset_id)"
                                    class="w-full p-2 font-mono text-sm bg-white border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                                ></textarea>
                                <div class="flex justify-end gap-2">
                                    <UButton
                                        icon="i-heroicons-x-mark"
                                        color="error"
                                        @click="cancelEdit(dataset.dataset_id)"
                                        >Cancel</UButton
                                    >
                                    <UButton
                                        icon="i-heroicons-check"
                                        color="success"
                                        @click="saveMetadataChanges(dataset.dataset_id)"
                                        >Save</UButton
                                    >
                                </div>
                            </div>
                            <div v-else class="space-y-3">
                                <div
                                    class="flex justify-between items-center text-xs text-gray-500 border-b border-gray-200 pb-2"
                                >
                                    <div class="flex items-center gap-4">
                                        <div class="flex items-center gap-1">
                                            <UIcon name="i-heroicons-plus-circle" class="w-3 h-3" />
                                            <span>Created:</span>
                                            <span class="font-medium">{{ formatTimestamp(dataset.created_at) }}</span>
                                        </div>
                                        <div v-if="dataset.last_edited_at" class="flex items-center gap-1">
                                            <UIcon name="i-heroicons-pencil-square" class="w-3 h-3" />
                                            <span>Last edited:</span>
                                            <span class="font-medium">{{
                                                formatTimestamp(dataset.last_edited_at)
                                            }}</span>
                                        </div>
                                    </div>
                                    <UButton
                                        icon="i-heroicons-pencil"
                                        size="xs"
                                        @click="enterEditMode(dataset.dataset_id, dataset.metadata)"
                                        >Edit</UButton
                                    >
                                </div>

                                <div
                                    v-if="dataset.metadata.description || dataset.metadata.comment"
                                    class="grid gap-3"
                                    :class="getGridClass(dataset.metadata)"
                                >
                                    <div v-if="dataset.metadata.description" class="space-y-1">
                                        <label class="text-sm font-medium text-gray-700">Description</label>
                                        <div class="bg-white rounded border px-2 py-1 text-sm text-gray-800">
                                            <p class="whitespace-pre-wrap">{{ dataset.metadata.description }}</p>
                                        </div>
                                    </div>
                                    <div v-if="dataset.metadata.comment" class="space-y-1">
                                        <label class="text-sm font-medium text-gray-700">Comment</label>
                                        <div class="bg-white rounded border px-2 py-1 text-sm text-gray-800">
                                            <p class="whitespace-pre-wrap">{{ dataset.metadata.comment }}</p>
                                        </div>
                                    </div>
                                </div>

                                <template v-for="[key, value] in getSortedMetadata(dataset.metadata)" :key="key">
                                    <div v-if="key === getFirstVectorKey(dataset.metadata)" class="clear-both w-full" />

                                    <div v-if="isLongStringField(key, value)" class="space-y-1">
                                        <label class="text-sm font-medium text-gray-700 capitalize">
                                            {{ formatFieldName(key) }}
                                        </label>
                                        <div class="bg-white rounded border p-2 text-xs text-gray-800">
                                            <code class="break-all">{{ value }}</code>
                                        </div>
                                    </div>

                                    <div v-else-if="isSizeField(key)" class="inline-block mr-3 mb-2">
                                        <UBadge color="neutral" variant="soft" size="md">
                                            <span class="font-medium">{{ formatFieldName(key) }}:</span>
                                            <span class="ml-1 font-normal">{{ formatSizeInGiB(value) }}</span>
                                        </UBadge>
                                    </div>

                                    <div v-else-if="isShortField(key, value)" class="inline-block mr-3 mb-2">
                                        <UBadge color="neutral" variant="soft" size="md">
                                            <span class="font-medium">{{ formatFieldName(key) }}:</span>
                                            <span class="ml-1 font-normal">{{ value }}</span>
                                        </UBadge>
                                    </div>

                                    <div
                                        v-else-if="isVectorField(value)"
                                        :class="
                                            formatVectorPreview(value as unknown[]).needsFullRow
                                                ? 'w-full space-y-1'
                                                : 'inline-block mr-3 mb-2 space-y-1'
                                        "
                                    >
                                        <label class="text-sm font-medium text-gray-700 capitalize">
                                            {{ formatFieldName(key) }}
                                            <span class="text-gray-500 font-normal ml-1 normal-case"
                                                >(len: {{ (value as unknown[]).length }})</span
                                            >
                                        </label>
                                        <div class="bg-white rounded border px-2 py-1 text-sm text-gray-800">
                                            <span class="break-all font-mono text-xs">
                                                {{ formatVectorPreview(value as unknown[]).preview }}
                                            </span>
                                        </div>
                                    </div>

                                    <div v-else class="space-y-1">
                                        <label class="text-sm font-medium text-gray-700 capitalize">
                                            {{ formatFieldName(key) }}
                                        </label>
                                        <div class="bg-white rounded border px-2 py-1 text-sm text-gray-800">
                                            <span>{{ value }}</span>
                                        </div>
                                    </div>
                                </template>
                            </div>
                        </div>
                    </div>
                </UCard>

                <!-- Loading states and load more controls -->
                <div v-if="shouldShowLoadingIndicatorDatasets" class="flex justify-center py-8">
                    <div class="flex items-center space-x-3 text-sm text-gray-600 dark:text-gray-400">
                        <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500" />
                        <span>Loading more results...</span>
                    </div>
                </div>

                <div v-else-if="shouldShowCompletionMessage" class="flex justify-center py-6">
                    <div class="text-center text-sm text-gray-500 dark:text-gray-400">
                        <UIcon name="i-heroicons-check-circle" class="inline mr-1" />
                        All {{ pagination.totalDatasets }} results loaded
                    </div>
                </div>
            </div>

            <!-- Pagination component (only in pagination mode) -->
            <div v-if="!infiniteScrollEnabled" class="flex justify-center mt-4 w-full">
                <UPagination
                    :page="pagination.currentPage"
                    :total="Math.ceil(pagination.totalDatasets / pagination.pageSize)"
                    size="sm"
                    @update:page="pagination.currentPage = $event"
                />
            </div>
        </div>

        <!-- No Results -->
        <UCard v-else class="text-center py-12 text-gray-600 dark:text-gray-400">
            <p class="text-lg font-medium">No datasets found.</p>
            <p class="text-sm">Try adjusting your search query. 🔎</p>
        </UCard>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from "vue";
import { useRoute } from "vue-router";
import { watchDebounced, useInfiniteScroll } from "@vueuse/core";

// Types (inline)
interface Dataset {
    dataset_id: number;
    name: string;
    metadata: Record<string, unknown>;
    created_at: string;
    last_edited_at?: string;
    accelerator_id?: number | null;
    stage_id?: number | null;
    campaign_id?: number | null;
    detector_id?: number | null;
    detector_name?: string | null;
    campaign_name?: string | null;
    stage_name?: string | null;
    accelerator_name?: string | null;
}

interface PaginatedResponse {
    total: number;
    items?: Dataset[];
    data?: Dataset[];
}

interface DropdownItem {
    id: number;
    name: string;
}

interface SearchState {
    isLoading: boolean;
    isLoadingMore: boolean;
    datasets: Dataset[];
    error: string | null;
    hasMore: boolean;
}

interface PaginationState {
    currentPage: number;
    pageSize: number;
    totalDatasets: number;
    totalPages: number;
    loadedPages: Set<number>;
}

interface SortState {
    sortBy: string;
    sortOrder: "asc" | "desc";
    availableFields: string[];
    isLoading: boolean;
}

interface SelectionState {
    selectedDatasets: Set<number>;
    expandedMetadata: Set<number>;
    isDownloading: boolean;
}

interface NavigationDropdown {
    items: DropdownItem[];
    isLoading: boolean;
    isOpen: boolean;
    icon: string;
    label: string;
    clearLabel: string;
    apiCall: (filters?: Record<string, string | undefined>) => Promise<DropdownItem[]>;
}

// Props
interface Props {
    initialFilters: Record<string, string>;
    routeParams?: string[];
}

const props = withDefaults(defineProps<Props>(), {
    routeParams: () => [],
});

// API Client (inline)
class ApiClient {
    public baseUrl: string;

    constructor() {
        const config = useRuntimeConfig();
        this.baseUrl = config.public.apiBaseUrl;
    }

    private async makeRequest<T>(url: string, options: RequestInit = {}, errorContext: string): Promise<T> {
        const shouldIncludeCredentials = url.includes("/authorized/");
        const fetchOptions: RequestInit = {
            ...options,
            ...(shouldIncludeCredentials && { credentials: "include" }),
            headers: {
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, fetchOptions);

            if (response.ok) {
                apiAvailable.value = true;
                const result = await response.json();
                return result;
            }
            const error: any = new Error(`${errorContext}: Server responded with status ${response.status}`);
            error.status = response.status;
            throw error;
        } catch (error) {
            // Only set API as unavailable on connection errors, not on 4xx/5xx
            if (
                error instanceof Error &&
                (error.message.includes("fetch failed") || error.message.includes("Failed to fetch"))
            ) {
                apiAvailable.value = false;
            }
            throw error;
        }
    }

    async searchDatasets(
        query: string,
        limit: number,
        offset: number,
        sortBy?: string,
        sortOrder?: "asc" | "desc",
    ): Promise<PaginatedResponse> {
        const params = new URLSearchParams({
            q: query,
            limit: String(limit),
            offset: String(offset),
        });

        if (sortBy) params.append("sort_by", sortBy);
        if (sortOrder) params.append("sort_order", sortOrder);

        return this.makeRequest<PaginatedResponse>(
            `${this.baseUrl}/query/?${params}`,
            {
                headers: {
                    "Cache-Control": "no-cache",
                    Pragma: "no-cache",
                    Expires: "0",
                },
            },
            "Failed to search datasets",
        );
    }

    async getNavigationOptions(
        entityType: "stage" | "campaign" | "detector" | "accelerator",
        filters?: Record<string, string | undefined>,
    ): Promise<DropdownItem[]> {
        const endpoint = `${entityType}s`;
        const url = new URL(`${this.baseUrl}/${endpoint}/`);

        if (filters) {
            Object.entries(filters).forEach(([key, value]) => {
                if (value?.trim()) {
                    url.searchParams.append(key, value);
                }
            });
        }

        return this.makeRequest<DropdownItem[]>(url.toString(), {}, `Failed to fetch ${entityType}s`);
    }

    async downloadDatasetsByIds(datasetIds: number[]): Promise<Dataset[]> {
        return this.makeRequest<Dataset[]>(
            `${this.baseUrl}/datasets/`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    dataset_ids: datasetIds,
                }),
            },
            "Failed to download datasets",
        );
    }

    async getSortingFields(): Promise<{ fields: string[]; count: number; info: string }> {
        return this.makeRequest<{ fields: string[]; count: number; info: string }>(
            `${this.baseUrl}/sorting-fields/`,
            {},
            "Failed to fetch sorting fields",
        );
    }

    async updateDataset(datasetId: number, metadata: Record<string, any>): Promise<Dataset> {
        const requestUrl = `${this.baseUrl}/authorized/datasets/${datasetId}`;
        return this.makeRequest<Dataset>(
            requestUrl,
            {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ metadata }),
            },
            "Failed to update dataset",
        );
    }
}

// Auth functionality (inline)
const AUTH_CHANNEL_NAME = "fcc-physics-auth-channel";
const AUTH_SUCCESS_MESSAGE = "authentication-successful";

function loginInNewTab() {
    const config = useRuntimeConfig();
    const redirectUrl = `${window.location.origin}/auth/callback`;
    const startUrl = `${config.public.apiBaseUrl}/authorized/oauth2/start?rd=${encodeURIComponent(redirectUrl)}`;
    window.open(startUrl, "_blank")?.focus();
}

function listenForAuthSuccess(onAuthSuccess: () => void) {
    const authChannel = new BroadcastChannel(AUTH_CHANNEL_NAME);
    const handleMessage = (event: MessageEvent) => {
        if (event.data === AUTH_SUCCESS_MESSAGE) {
            onAuthSuccess();
            authChannel.close();
        }
    };
    authChannel.onmessage = handleMessage;
    return () => authChannel.close();
}

// Route and initial setup
const route = useRoute();
const initialQuery = (route.query.q as string) || "";
const apiClient = new ApiClient();
const toast = useToast();

// Core reactive state
const userSearchQuery = ref(initialQuery);
const infiniteScrollEnabled = ref(true);
const activeFilters = ref(props.initialFilters);
const isFilterUpdateInProgress = ref(false);
const isLoadingActive = ref(false);
const shouldShowLoadingIndicator = ref(false);
const apiAvailable = ref(true);
const isInitialized = ref(false);

let delayTimeoutId: NodeJS.Timeout | null = null;
let currentRequestController: AbortController | null = null;

// Search Controls state
const isPermalinkCopyInProgress = ref(false);
const showLinkCopiedFeedback = ref(false);
const codeClass = "bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-xs font-mono";

// Search state
const searchState = reactive<SearchState>({
    isLoading: false,
    isLoadingMore: false,
    datasets: [],
    error: null,
    hasMore: true,
});

// Pagination state
const pagination = reactive<PaginationState>({
    currentPage: 1,
    pageSize: 20,
    totalDatasets: 0,
    totalPages: 0,
    loadedPages: new Set<number>(),
});

// Sort state
const sortState = reactive<SortState>({
    sortBy: "last_edited_at",
    sortOrder: "desc",
    availableFields: [],
    isLoading: false,
});

// Selection state
const selectionState = reactive<SelectionState>({
    selectedDatasets: new Set<number>(),
    expandedMetadata: new Set<number>(),
    isDownloading: false,
});

// Metadata editing state
const metadataEditState = reactive<Record<number, { isEditing: boolean; json: string; authListener?: () => void }>>({});

// Navigation configuration
const navigationConfig = {
    stage: {
        icon: "i-heroicons-cpu-chip",
        label: "Stage",
        clearLabel: "Clear Stage",
        apiCall: (filters?: Record<string, string | undefined>) => apiClient.getNavigationOptions("stage", filters),
    },
    campaign: {
        icon: "i-heroicons-calendar-days",
        label: "Campaign",
        clearLabel: "Clear Campaign",
        apiCall: (filters?: Record<string, string | undefined>) => apiClient.getNavigationOptions("campaign", filters),
    },
    detector: {
        icon: "i-heroicons-beaker",
        label: "Detector",
        clearLabel: "Clear Detector",
        apiCall: (filters?: Record<string, string | undefined>) => apiClient.getNavigationOptions("detector", filters),
    },
} as const;

type DropdownType = keyof typeof navigationConfig;
const dropdownKeys = Object.keys(navigationConfig) as DropdownType[];

// Navigation state
const dropdowns = reactive<Record<DropdownType, NavigationDropdown>>({
    stage: {
        items: [],
        isLoading: false,
        isOpen: false,
        ...navigationConfig.stage,
    },
    campaign: {
        items: [],
        isLoading: false,
        isOpen: false,
        ...navigationConfig.campaign,
    },
    detector: {
        items: [],
        isLoading: false,
        isOpen: false,
        ...navigationConfig.detector,
    },
});

// Loading delay functions
const loadingDelayMap = new Map<DropdownType, any>();

// Initialize loading delay for each dropdown type
Object.keys(dropdowns).forEach((type) => {
    loadingDelayMap.set(type as DropdownType, {
        shouldShowLoading: ref(false),
        startLoading: () => {
            setTimeout(() => {
                const delay = loadingDelayMap.get(type as DropdownType);
                if (delay) {
                    delay.shouldShowLoading.value = true;
                }
            }, 500);
        },
        stopLoading: () => {
            const delay = loadingDelayMap.get(type as DropdownType);
            if (delay) {
                delay.shouldShowLoading.value = false;
            }
        },
    });
});

// Computed values
const urlFilterQuery = computed(() => {
    return Object.entries(activeFilters.value)
        .map(([field, value]) => {
            const searchField = field.replace("_name", "");
            return `${searchField}="${value}"`;
        })
        .join(" AND ");
});

const combinedSearchQuery = computed(() => {
    const urlFilterPart = urlFilterQuery.value;
    const userInputPart = userSearchQuery.value.trim();

    if (urlFilterPart && userInputPart) {
        return `${urlFilterPart} AND ${userInputPart}`;
    }
    return urlFilterPart || userInputPart;
});

const searchPlaceholderText = computed(() => {
    return urlFilterQuery.value ? "Add additional search terms..." : 'e.g., detector="IDEA" AND metadata.status="done"';
});

const showFilterNote = computed(() => !!urlFilterQuery.value);

const canCopyLink = computed(() => {
    return !!userSearchQuery.value || Object.keys(activeFilters.value).length > 0;
});

const currentDisplayRange = computed(() => {
    if (infiniteScrollEnabled.value) {
        const totalDisplayed = searchState.datasets.length;
        const start = totalDisplayed > 0 ? 1 : 0;
        return { start, end: totalDisplayed, total: pagination.totalDatasets };
    } else {
        const start = (pagination.currentPage - 1) * pagination.pageSize + 1;
        const end = Math.min(pagination.currentPage * pagination.pageSize, pagination.totalDatasets);
        return {
            start: searchState.datasets.length > 0 ? start : 0,
            end,
            total: pagination.totalDatasets,
        };
    }
});

const canLoadMore = computed(() => {
    return (
        searchState.hasMore &&
        infiniteScrollEnabled.value &&
        !searchState.isLoading &&
        !searchState.isLoadingMore &&
        !isFilterUpdateInProgress.value
    );
});

const sortingFieldOptions = computed(() => {
    return sortState.availableFields.map((field) => ({
        label: formatFieldLabel(field),
        value: field,
    }));
});

const showLoadingSkeleton = computed(() => {
    return searchState.isLoading && (shouldShowLoadingIndicator.value || searchState.datasets.length === 0);
});

// Navigation computed
const currentPath = computed(() => {
    const pathObj: Record<DropdownType, string | null> = {} as Record<DropdownType, string | null>;
    dropdownKeys.forEach((type, index) => {
        pathObj[type] = props.routeParams[index] || null;
    });
    return pathObj;
});

const visibleDropdowns = computed(() => {
    const visible: DropdownType[] = [];
    visible.push("stage");
    if (currentPath.value.stage) {
        visible.push("campaign");
    }
    if (currentPath.value.stage && currentPath.value.campaign) {
        visible.push("detector");
    }
    return visible;
});

const activeDropdowns = computed(() => {
    const filtered: Record<DropdownType, NavigationDropdown> = {} as Record<DropdownType, NavigationDropdown>;

    visibleDropdowns.value.forEach((type) => {
        if (dropdowns[type]) {
            filtered[type] = dropdowns[type];
        }
    });

    return filtered;
});

// Selection computed
const selectedCount = computed(() => selectionState.selectedDatasets.size);

const allDatasetsSelected = computed(() => {
    const currentDatasetIds = searchState.datasets.map((dataset) => dataset.dataset_id);
    return currentDatasetIds.length > 0 && currentDatasetIds.every((id) => selectionState.selectedDatasets.has(id));
});

const allMetadataExpanded = computed(() => {
    const currentDatasetIds = searchState.datasets.map((dataset) => dataset.dataset_id);
    return currentDatasetIds.length > 0 && currentDatasetIds.every((id) => selectionState.expandedMetadata.has(id));
});

// Loading state computed
const shouldShowLoadingIndicatorDatasets = computed(() => {
    return searchState.isLoadingMore && infiniteScrollEnabled.value && canLoadMore.value;
});

const shouldShowCompletionMessage = computed(() => {
    return !searchState.hasMore && searchState.datasets.length > 0 && pagination.totalDatasets > 0;
});

// Utility functions
const isClient = () => typeof window !== "undefined";

function formatFieldLabel(field: string): string {
    if (field.startsWith("metadata.")) {
        const metadataKey = field.replace("metadata.", "");
        return `Metadata: ${metadataKey.replace(/-/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}`;
    }
    return field
        .replace(/_/g, " ")
        .replace(/\b\w/g, (l) => l.toUpperCase())
        .replace(" Name", "");
}

function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString();
}

function formatMetadataValue(value: unknown): string {
    if (typeof value === "object" && value !== null) {
        return JSON.stringify(value, null, 2);
    }
    return String(value);
}

function createDatasetDownloadFilename(datasetCount: number): string {
    const now = new Date();
    const timestamp = now
        .toISOString()
        .slice(0, 19)
        .replace(/[-T:]/g, (match) => (match === "T" ? "_" : "-"));
    return `fcc_physics_datasets-${datasetCount}-datasets-${timestamp}.json`;
}

function downloadAsJsonFile(data: unknown, filename: string): void {
    const jsonContent = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonContent], { type: "application/json" });
    const downloadUrl = URL.createObjectURL(blob);

    const downloadLink = document.createElement("a");
    downloadLink.href = downloadUrl;
    downloadLink.download = filename;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
    URL.revokeObjectURL(downloadUrl);
}

function getBadgeColor(type: DropdownType): "success" | "warning" | "info" | "primary" {
    const colorMap: Record<DropdownType, "success" | "warning" | "info"> = {
        stage: "success",
        campaign: "warning",
        detector: "info",
    };
    return colorMap[type] || "primary";
}

function getBadgeItems(dataset: Dataset) {
    return [
        {
            key: "stage",
            label: "Stage",
            value: dataset.stage_name,
            color: "success" as const,
            widthClass: "w-42",
        },
        {
            key: "campaign",
            label: "Campaign",
            value: dataset.campaign_name,
            color: "warning" as const,
            widthClass: "w-60",
        },
        {
            key: "detector",
            label: "Detector",
            value: dataset.detector_name,
            color: "info" as const,
            widthClass: "w-32",
        },
        {
            key: "accelerator",
            label: "Accelerator",
            value: dataset.accelerator_name,
            color: "secondary" as const,
            widthClass: "w-40",
        },
    ];
}

// Metadata utility functions and constants
const LONG_STRING_FIELDS = ["path", "software-stack", "description"];
const EXCLUDED_FIELDS = new Set(["description", "comment"]);
const FIELD_DISPLAY_ORDER = ["software-stack", "path"];

function getGridClass(metadata: Record<string, unknown>): string {
    const hasDescription = !!metadata.description;
    const hasComment = !!metadata.comment;
    return hasDescription && hasComment ? "grid-cols-2" : "grid-cols-1";
}

function getTextareaRows(datasetId: number): number {
    const editState = metadataEditState[datasetId];
    if (!editState) return 10;
    const lineCount = editState.json.split("\n").length;
    return Math.max(10, Math.min(lineCount + 1, 25));
}

function isLongStringField(key: string, value: unknown): boolean {
    if (typeof value !== "string") return false;
    return LONG_STRING_FIELDS.includes(key.toLowerCase()) || value.length > 50;
}

function isShortField(key: string, value: unknown): boolean {
    if (typeof value === "number" || typeof value === "boolean") return true;
    return typeof value === "string" && value.length <= 20;
}

function isSizeField(key: string): boolean {
    return key.toLowerCase() === "size";
}

function isVectorField(value: unknown): boolean {
    return (
        Array.isArray(value) &&
        value.length > 0 &&
        value.every((item) => ["number", "string", "boolean"].includes(typeof item))
    );
}

function formatSizeInGiB(bytes: unknown): string {
    const bytesNumber = Number(bytes);
    if (isNaN(bytesNumber) || bytesNumber < 0) return "N/A";
    const gigabytes = bytesNumber / (1024 * 1024 * 1024);
    return `${gigabytes.toFixed(2)} GiB`;
}

function formatTimestamp(timestamp: string): string {
    try {
        const date = new Date(timestamp);
        return date.toLocaleString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
            timeZoneName: "short",
        });
    } catch {
        return timestamp;
    }
}

function formatVectorPreview(value: unknown[]): { preview: string; needsFullRow: boolean } {
    const firstFive = value.slice(0, 5);
    const preview =
        firstFive
            .map((item) => {
                if (typeof item === "number") {
                    return Number.isInteger(item) ? item.toString() : item.toFixed(3);
                }
                return String(item);
            })
            .join(", ") + (value.length > 5 ? ", ..." : "");

    const avgFieldNameLength = 20;
    const lengthIndicatorLength = String(value.length).length + 3;
    const totalContentLength = avgFieldNameLength + preview.length + lengthIndicatorLength;
    const hasLongItems = firstFive.some((item) => String(item).length > 30);

    const needsFullRow = totalContentLength > 60 || hasLongItems || preview.length > 50;
    return { preview, needsFullRow };
}

function getSortedMetadata(metadata: Record<string, unknown>): [string, unknown][] {
    const entries = Object.entries(metadata);
    const filteredEntries = entries.filter(([key]) => !EXCLUDED_FIELDS.has(key));

    const endFields: [string, unknown][] = [];
    const regularFields: [string, unknown][] = [];
    const vectorFields: [string, unknown][] = [];

    filteredEntries.forEach(([key, value]) => {
        if (FIELD_DISPLAY_ORDER.includes(key)) {
            endFields.push([key, value]);
        } else if (isVectorField(value)) {
            vectorFields.push([key, value]);
        } else {
            regularFields.push([key, value]);
        }
    });

    regularFields.sort(([a], [b]) => a.localeCompare(b));

    vectorFields.sort(([keyA, valueA], [keyB, valueB]) => {
        const previewA = formatVectorPreview(valueA as unknown[]);
        const previewB = formatVectorPreview(valueB as unknown[]);

        if (previewA.needsFullRow !== previewB.needsFullRow) {
            return previewA.needsFullRow ? 1 : -1;
        }
        return keyA.localeCompare(keyB);
    });

    endFields.sort(([a], [b]) => FIELD_DISPLAY_ORDER.indexOf(a) - FIELD_DISPLAY_ORDER.indexOf(b));

    return [...regularFields, ...endFields, ...vectorFields];
}

function getFirstVectorKey(metadata: Record<string, unknown>): string | null {
    const vectors = getSortedMetadata(metadata).filter(([, value]) => isVectorField(value));
    return vectors.length > 0 ? vectors[0][0] : null;
}

// Loading delay functions
function startLoading() {
    isLoadingActive.value = true;
    delayTimeoutId = setTimeout(() => {
        shouldShowLoadingIndicator.value = true;
    }, 300);
}

function stopLoading() {
    isLoadingActive.value = false;
    shouldShowLoadingIndicator.value = false;
    if (delayTimeoutId) {
        clearTimeout(delayTimeoutId);
        delayTimeoutId = null;
    }
}

// Navigation functions
function toggleDropdown(type: DropdownType) {
    const wasOpen = dropdowns[type].isOpen;
    closeAllDropdowns();
    if (!wasOpen) {
        dropdowns[type].isOpen = true;
    }
}

function closeAllDropdowns() {
    visibleDropdowns.value.forEach((type) => {
        if (dropdowns[type]) {
            dropdowns[type].isOpen = false;
        }
    });
}

function buildFiltersForDropdown(targetType: DropdownType): Record<string, string> {
    const current = currentPath.value;
    const filters: Record<string, string> = {};

    for (const type of dropdownKeys) {
        if (type !== targetType && current[type]) {
            filters[`${type}_name`] = current[type];
        }
    }

    return filters;
}

async function loadDropdownData() {
    // Don't load on server side
    if (!isClient()) return;

    const loadPromises = visibleDropdowns.value.map(async (type) => {
        const dropdown = dropdowns[type];
        const loadingState = loadingDelayMap.get(type);

        if (!loadingState || !dropdown) return;

        // Don't reload if already loaded or currently loading
        if (dropdown.items.length > 0 || dropdown.isLoading) {
            return;
        }

        loadingState.startLoading();

        // Set dropdown loading state when delay threshold is reached
        const stopWatching = watch(
            loadingState.shouldShowLoading,
            (shouldShow) => {
                dropdown.isLoading = shouldShow;
            },
            { immediate: true },
        );

        try {
            const filters = buildFiltersForDropdown(type);
            dropdown.items = await dropdown.apiCall(filters);
        } catch (error) {
            console.error(`Error loading ${type}:`, error);
            dropdown.items = [];
            // Don't retry immediately on error
        } finally {
            loadingState.stopLoading();
            stopWatching(); // Clean up the watcher
        }
    });

    // Load all visible dropdowns in parallel for better performance
    await Promise.allSettled(loadPromises);
}

function navigateToPath(type: DropdownType, value: string) {
    const current = currentPath.value;
    const pathParts = dropdownKeys.map((t) => current[t]);
    const typeIndex = dropdownKeys.indexOf(type);

    const newPathParts = pathParts.slice(0, typeIndex);
    newPathParts.push(value);

    const newPath = `/${newPathParts.filter((p) => p).join("/")}`;

    // Use Nuxt's navigateTo composable
    navigateTo(newPath);
}

function clearSelectionPath(type: DropdownType) {
    const current = currentPath.value;
    const pathParts = dropdownKeys.map((t) => current[t]);
    const typeIndex = dropdownKeys.indexOf(type);

    const newPathParts = pathParts.slice(0, typeIndex).filter((p) => p);
    const newPath = newPathParts.length === 0 ? "/" : `/${newPathParts.join("/")}`;

    // Use Nuxt's navigateTo composable
    navigateTo(newPath);
}

// Search Controls functions
function openQueryDocumentation() {
    window.open("https://cloud.google.com/logging/docs/view/logging-query-language", "_blank");
}

function showSuccessNotification() {
    showLinkCopiedFeedback.value = true;
    setTimeout(() => {
        showLinkCopiedFeedback.value = false;
    }, 2000);
}

async function copyToClipboard(text: string): Promise<void> {
    try {
        await navigator.clipboard.writeText(text);
    } catch {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.opacity = "0";
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand("copy");
        document.body.removeChild(textArea);
    }
}

function generatePermalinkUrl(): string {
    if (!isClient()) return "";
    const currentUrl = new URL(window.location.href);
    const params = new URLSearchParams();

    if (userSearchQuery.value.trim()) params.set("q", userSearchQuery.value.trim());
    if (sortState.sortBy !== "last_edited_at") params.set("sort_by", sortState.sortBy);
    if (sortState.sortOrder !== "desc") params.set("sort_order", sortState.sortOrder);

    const baseUrl = `${currentUrl.origin}${currentUrl.pathname}`;
    const queryString = params.toString();
    return queryString ? `${baseUrl}?${queryString}` : baseUrl;
}

async function handleCopyPermalink() {
    if (isPermalinkCopyInProgress.value) return;

    try {
        isPermalinkCopyInProgress.value = true;
        const permalinkUrl = generatePermalinkUrl();
        await copyToClipboard(permalinkUrl);
        showSuccessNotification();
    } catch (error) {
        console.error("Failed to copy permalink:", error);
    } finally {
        isPermalinkCopyInProgress.value = false;
    }
}

// Search functions
async function performSearch(resetResults = true) {
    // Don't search on server side
    if (!isClient()) return;

    if (!apiAvailable.value) {
        console.warn("API is unavailable, skipping search");
        return;
    }

    if (currentRequestController) {
        currentRequestController.abort();
    }
    currentRequestController = new AbortController();
    const searchQuery = combinedSearchQuery.value.trim();
    const isInitialLoad = resetResults;

    if (isInitialLoad) {
        searchState.isLoading = true;
        searchState.datasets = [];
        pagination.loadedPages.clear();
        if (infiniteScrollEnabled.value) {
            pagination.currentPage = 1;
        }
    } else {
        searchState.isLoadingMore = true;
    }
    searchState.error = null;

    try {
        const pageToLoad = isInitialLoad
            ? infiniteScrollEnabled.value
                ? 1
                : pagination.currentPage
            : pagination.currentPage;
        const offset = (pageToLoad - 1) * pagination.pageSize;
        const queryToSend = searchQuery || "*";

        const response: PaginatedResponse = await apiClient.searchDatasets(
            queryToSend,
            pagination.pageSize,
            offset,
            sortState.sortBy,
            sortState.sortOrder,
        );

        if (currentRequestController?.signal.aborted) return;

        const responseDatasets = response.data || response.items || [];

        if (isInitialLoad || !infiniteScrollEnabled.value) {
            searchState.datasets = responseDatasets;
            pagination.loadedPages.clear();
            pagination.loadedPages.add(pageToLoad);
        } else {
            searchState.datasets.push(...responseDatasets);
            pagination.loadedPages.add(pageToLoad);
        }

        pagination.totalDatasets = response.total;
        pagination.totalPages = Math.ceil(response.total / pagination.pageSize);
        searchState.hasMore = pagination.currentPage < pagination.totalPages;
    } catch (error) {
        if (currentRequestController?.signal.aborted) return;
        console.error("Search failed:", error);
        searchState.error = error instanceof Error ? error.message : "Failed to fetch datasets.";
        if (isInitialLoad) {
            searchState.datasets = [];
            pagination.totalDatasets = 0;
            pagination.totalPages = 0;
        }
        searchState.hasMore = false;
    } finally {
        if (!currentRequestController?.signal.aborted) {
            if (isInitialLoad) {
                searchState.isLoading = false;
            } else {
                searchState.isLoadingMore = false;
            }
        }
    }
}

async function fetchSortingFields() {
    // Don't fetch on server side
    if (!isClient()) return;

    if (!apiAvailable.value) {
        console.warn("API is unavailable, skipping sorting fields fetch");
        return;
    }

    // Prevent duplicate calls - only allow if no fields loaded yet
    if (sortState.availableFields.length > 0) {
        return;
    }

    try {
        sortState.isLoading = true;
        const response = await apiClient.getSortingFields();
        sortState.availableFields = response.fields;
    } catch (error) {
        console.error("Error fetching sorting fields:", error);
    } finally {
        sortState.isLoading = false;
    }
}

function executeSearch() {
    pagination.currentPage = 1;
    performSearch(true);
    updateUrlWithSearchState();
}

function handleSearch() {
    executeSearch();
}

async function loadMoreData() {
    // Prevent loading more data if the first page isn't full, which can happen on initial load
    if (pagination.currentPage === 1 && searchState.datasets.length < pagination.pageSize) {
        return;
    }

    if (isFilterUpdateInProgress.value || searchState.isLoadingMore || !canLoadMore.value || !searchState.hasMore) {
        return;
    }
    pagination.currentPage += 1;
    await performSearch(false);
}

function toggleMode() {
    infiniteScrollEnabled.value = !infiniteScrollEnabled.value;
    pagination.currentPage = 1;
    performSearch(true);
}

function toggleSortOrder() {
    sortState.sortOrder = sortState.sortOrder === "asc" ? "desc" : "asc";
}

function handlePageSizeChange() {
    pagination.currentPage = 1;
    performSearch(true);
}

function updateUrlWithSearchState() {
    if (!isClient()) return;
    const newUrl = generatePermalinkUrl();
    if (newUrl !== window.location.href) {
        window.history.replaceState({}, "", newUrl);
    }
}

function updateFilters(newFilters: Record<string, string>) {
    if (JSON.stringify(activeFilters.value) !== JSON.stringify(newFilters)) {
        isFilterUpdateInProgress.value = true;
        activeFilters.value = { ...newFilters };
    }
}

// Selection functions
function toggleDatasetSelection(datasetId: number) {
    if (selectionState.selectedDatasets.has(datasetId)) {
        selectionState.selectedDatasets.delete(datasetId);
    } else {
        selectionState.selectedDatasets.add(datasetId);
    }
}

function toggleSelectAll() {
    const currentDatasetIds = searchState.datasets.map((d) => d.dataset_id);
    const allSelected = currentDatasetIds.every((id) => selectionState.selectedDatasets.has(id));

    if (allSelected) {
        currentDatasetIds.forEach((id) => selectionState.selectedDatasets.delete(id));
    } else {
        currentDatasetIds.forEach((id) => selectionState.selectedDatasets.add(id));
    }
}

function toggleMetadata(datasetId: number) {
    if (selectionState.expandedMetadata.has(datasetId)) {
        selectionState.expandedMetadata.delete(datasetId);
    } else {
        selectionState.expandedMetadata.add(datasetId);
    }
}

function toggleAllMetadata() {
    const currentDatasetIds = searchState.datasets.map((dataset) => dataset.dataset_id);
    const allExpanded =
        currentDatasetIds.length > 0 && currentDatasetIds.every((id) => selectionState.expandedMetadata.has(id));

    if (allExpanded) {
        currentDatasetIds.forEach((id) => selectionState.expandedMetadata.delete(id));
    } else {
        currentDatasetIds.forEach((id) => selectionState.expandedMetadata.add(id));
    }
}

function clearMetadataExpansions() {
    selectionState.expandedMetadata.clear();
}

function isDatasetSelected(datasetId: number): boolean {
    return selectionState.selectedDatasets.has(datasetId);
}

function isMetadataExpanded(datasetId: number): boolean {
    return selectionState.expandedMetadata.has(datasetId);
}

async function downloadSelectedDatasets() {
    const selectedDatasetIds = Array.from(selectionState.selectedDatasets);
    if (selectedDatasetIds.length === 0) return;

    selectionState.isDownloading = true;
    try {
        const datasetsToDownload = await apiClient.downloadDatasetsByIds(selectedDatasetIds);

        if (datasetsToDownload.length > 0) {
            const filename = createDatasetDownloadFilename(datasetsToDownload.length);
            downloadAsJsonFile(datasetsToDownload, filename);
        }
    } catch (error) {
        console.error("Failed to download datasets:", error);
    } finally {
        selectionState.isDownloading = false;
    }
}

function handleRowClick(event: MouseEvent, datasetId: number) {
    // Don't trigger row click if text is being selected
    const selection = window.getSelection();
    if (selection && selection.toString().length > 0) {
        return;
    }

    // Don't trigger row click for interactive elements
    const target = event.target as HTMLElement;
    if (target.closest("button, a, input")) {
        return;
    }

    toggleMetadata(datasetId);
}

// Navigation click outside handler
function handleClickOutside(event: Event) {
    const target = event.target as HTMLElement;
    if (!target.closest(".relative")) {
        closeAllDropdowns();
    }
}

// Watchers
watch(
    () => searchState.isLoading,
    (isLoading) => {
        if (isLoading) {
            startLoading();
        } else {
            stopLoading();
        }
    },
    { immediate: true },
);

watch(
    () => pagination.currentPage,
    (newPage, oldPage) => {
        if (!infiniteScrollEnabled.value && newPage !== oldPage) {
            pagination.currentPage = Math.max(1, Math.min(newPage, pagination.totalPages));
            if (!infiniteScrollEnabled.value) {
                performSearch(true);
            }
        }
    },
);

watch([() => sortState.sortBy, () => sortState.sortOrder], () => {
    pagination.currentPage = 1;
    performSearch(true);
    updateUrlWithSearchState();
});

watchDebounced(
    activeFilters,
    () => {
        isFilterUpdateInProgress.value = true;
        pagination.currentPage = 1;
        performSearch(true).finally(() => {
            isFilterUpdateInProgress.value = false;
        });
    },
    { debounce: 200, deep: true, immediate: false },
);

watch(
    () => searchState.datasets,
    () => clearMetadataExpansions(),
);

watch(
    () => pagination.currentPage,
    () => clearMetadataExpansions(),
);

watchDebounced(
    () => props.initialFilters,
    (newFilters, oldFilters) => {
        const filtersChanged = JSON.stringify(newFilters) !== JSON.stringify(oldFilters);
        if (filtersChanged || oldFilters === undefined) {
            updateFilters(newFilters);
            clearMetadataExpansions();
        }
    },
    { debounce: 50, deep: true, immediate: false },
);

// Only load dropdown data when the path actually changes
watch(
    currentPath,
    (newPath, oldPath) => {
        // Clear dependent dropdown items when path changes
        if (oldPath) {
            dropdownKeys.forEach((type, index) => {
                if (newPath[type] !== oldPath[type]) {
                    // Clear this dropdown and all subsequent ones
                    for (let i = index; i < dropdownKeys.length; i++) {
                        dropdowns[dropdownKeys[i]].items = [];
                    }
                }
            });
        }
        loadDropdownData();
    },
    { deep: true, immediate: false },
);

// Infinite scroll setup
if (isClient()) {
    useInfiniteScroll(window, () => loadMoreData(), {
        distance: 200,
        canLoadMore: () => canLoadMore.value,
    });
}

// Lifecycle
onMounted(async () => {
    // Use Nuxt's process.client check for SSR compatibility
    if (!process.client) return;

    // Wait for next tick to ensure component is fully mounted
    await nextTick();

    // Prevent double initialization in Nuxt.js SSR hydration
    if (isInitialized.value) {
        return;
    }

    isInitialized.value = true;

    await fetchSortingFields();

    document.addEventListener("click", handleClickOutside);

    // Initialize filters from props first
    if (Object.keys(props.initialFilters).length > 0) {
        updateFilters(props.initialFilters);
    }

    // Load dropdown data
    await loadDropdownData();

    // Automatically perform search if query or filters are present in URL
    if ((userSearchQuery.value && userSearchQuery.value.trim() !== "") || Object.keys(activeFilters.value).length > 0) {
        performSearch(true);
    }
});

onUnmounted(() => {
    if (currentRequestController) {
        currentRequestController.abort();
    }
    if (delayTimeoutId) {
        clearTimeout(delayTimeoutId);
        delayTimeoutId = null;
    }
    document.removeEventListener("click", handleClickOutside);

    // Clean up any active auth listeners
    Object.values(metadataEditState).forEach((editState) => {
        if (editState.authListener) {
            editState.authListener();
        }
    });
});

// Metadata editing functions
function enterEditMode(datasetId: number, metadata: Record<string, unknown>) {
    metadataEditState[datasetId] = {
        isEditing: true,
        json: JSON.stringify(metadata, null, 2),
    };

    // Set up authentication listener
    metadataEditState[datasetId].authListener = listenForAuthSuccess(() => {
        console.log("Authentication successful, you can now save metadata changes");
    });
}

function cancelEdit(datasetId: number) {
    if (metadataEditState[datasetId]?.authListener) {
        metadataEditState[datasetId].authListener?.();
    }
    delete metadataEditState[datasetId];
}

async function saveMetadataChanges(datasetId: number) {
    const editState = metadataEditState[datasetId];
    if (!editState) return;

    try {
        const parsedMetadata = JSON.parse(editState.json);

        // Call the backend API to save metadata
        await apiClient.updateDataset(datasetId, parsedMetadata);

        toast.add({
            title: "Success",
            description: "Dataset metadata updated successfully.",
            color: "success",
        });

        // Update the dataset in the local state
        const datasetIndex = searchState.datasets.findIndex((d) => d.dataset_id === datasetId);
        if (datasetIndex !== -1) {
            searchState.datasets[datasetIndex].metadata = parsedMetadata;
            searchState.datasets[datasetIndex].last_edited_at = new Date().toISOString();
        }

        // Remove any existing login prompt toast
        toast.remove("login-prompt-toast");

        // Clean up auth listener if it exists
        if (editState.authListener) {
            editState.authListener();
        }

        // Exit edit mode
        delete metadataEditState[datasetId];
    } catch (error: any) {
        const isCorsError = error instanceof TypeError && error.message === "Failed to fetch";

        if (error.status === 401 || error.status === 403 || isCorsError) {
            toast.add({
                id: "login-prompt-toast",
                title: "Login Required",
                description: "Please complete your login in the new tab. We will retry saving automatically.",
                progress: false,
                color: "info",
                actions: [
                    {
                        label: "Cancel",
                        onClick: () => {
                            if (editState.authListener) {
                                editState.authListener();
                            }
                            toast.remove("login-prompt-toast");
                        },
                    },
                ],
            });

            // Set up auth listener for retry
            editState.authListener = listenForAuthSuccess(() => {
                toast.add({
                    title: "Login Successful!",
                    description: "Retrying your save operation...",
                    color: "success",
                });
                saveMetadataChanges(datasetId);
            });

            loginInNewTab();
        } else {
            toast.add({
                title: "Error Saving Metadata",
                description: error.message || "An unknown error occurred. Please check the JSON format and try again.",
                color: "error",
            });
            console.error("Failed to save metadata:", error);
        }
    }
}

// Utility function to format field names
const formatFieldName = (key: string): string => {
    return key
        .split("_")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
};
</script>
