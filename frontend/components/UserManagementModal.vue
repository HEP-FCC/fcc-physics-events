<template>
    <UModal
        v-model:open="isOpen"
        title="User Management"
        :transition="true"
        :close="{
            color: 'neutral',
            variant: 'ghost',
            size: 'xs',
            class: 'w-6 h-6 p-1 hover:bg-gray-100 rounded cursor-pointer shrink-0 flex items-center justify-center',
        }"
    >
        <UButton
            class="cursor-pointer"
            icon="i-heroicons-users"
            color="neutral"
            variant="ghost"
            :label="iconOnly ? undefined : 'Users'"
            @click="isOpen = true"
        />

        <template #body>
            <div class="space-y-6">
                <!-- Grant editor -->
                <div class="space-y-2">
                    <h3 class="text-sm font-medium text-deep-blue-900">Grant Editor Role</h3>
                    <div class="flex items-center gap-2">
                        <UInput
                            v-model="newEditorUsername"
                            placeholder="CERN username"
                            class="flex-1"
                            :disabled="isGranting"
                            @keyup.enter="grantEditor"
                        />
                        <UButton
                            color="primary"
                            :loading="isGranting"
                            :disabled="!newEditorUsername.trim()"
                            class="cursor-pointer"
                            @click="grantEditor"
                        >
                            Grant
                        </UButton>
                    </div>
                </div>

                <!-- Current editors -->
                <div class="space-y-2">
                    <h3 class="text-sm font-medium text-deep-blue-900">Current Editors</h3>
                    <div v-if="isLoading" class="text-sm text-deep-blue-400">Loading...</div>
                    <div v-else-if="editors.length === 0" class="text-sm text-deep-blue-400">
                        No editors granted yet.
                    </div>
                    <ul v-else class="divide-y divide-gray-200 border border-gray-200 rounded-md">
                        <li
                            v-for="editor in editors"
                            :key="editor.cern_username"
                            class="flex items-center justify-between px-3 py-2"
                        >
                            <div>
                                <div class="text-sm font-medium text-deep-blue-900">
                                    {{ editor.cern_username }}
                                </div>
                                <div class="text-xs text-deep-blue-400">
                                    Granted by {{ editor.granted_by }} on
                                    {{ new Date(editor.granted_at).toLocaleDateString() }}
                                </div>
                            </div>
                            <UButton
                                color="error"
                                variant="ghost"
                                size="xs"
                                class="cursor-pointer"
                                :loading="revokingUsername === editor.cern_username"
                                @click="revokeEditor(editor.cern_username)"
                            >
                                Revoke
                            </UButton>
                        </li>
                    </ul>
                </div>

                <!-- Status message -->
                <div v-if="statusMessage" class="text-xs" :class="statusMessageClass">
                    {{ statusMessage }}
                </div>
            </div>
        </template>
    </UModal>
</template>

<script setup lang="ts">
interface Props {
    iconOnly?: boolean;
}

withDefaults(defineProps<Props>(), {
    iconOnly: false,
});

interface EditorGrant {
    cern_username: string;
    granted_by: string;
    granted_at: string;
}

const { listEditors, grantEditorRole, revokeEditorRole } = useApiClient();

const isOpen = ref(false);
const editors = ref<EditorGrant[]>([]);
const isLoading = ref(false);
const isGranting = ref(false);
const revokingUsername = ref<string | null>(null);
const newEditorUsername = ref("");
const statusMessage = ref("");
const statusMessageClass = ref("");

const showStatus = (message: string, type: "success" | "error") => {
    statusMessage.value = message;
    statusMessageClass.value = type === "success" ? "text-green-600" : "text-energy-600";
};

const loadEditors = async () => {
    isLoading.value = true;
    try {
        editors.value = await listEditors();
    } catch (error) {
        console.error("Failed to load editors:", error);
        showStatus("Failed to load the editor list.", "error");
    } finally {
        isLoading.value = false;
    }
};

const grantEditor = async () => {
    const username = newEditorUsername.value.trim();
    if (!username) return;

    isGranting.value = true;
    try {
        await grantEditorRole(username);
        newEditorUsername.value = "";
        showStatus(`Granted editor role to ${username}.`, "success");
        await loadEditors();
    } catch (error) {
        console.error("Failed to grant editor role:", error);
        showStatus(`Failed to grant editor role to ${username}.`, "error");
    } finally {
        isGranting.value = false;
    }
};

const revokeEditor = async (username: string) => {
    revokingUsername.value = username;
    try {
        await revokeEditorRole(username);
        showStatus(`Revoked editor role from ${username}.`, "success");
        await loadEditors();
    } catch (error) {
        console.error("Failed to revoke editor role:", error);
        showStatus(`Failed to revoke editor role from ${username}.`, "error");
    } finally {
        revokingUsername.value = null;
    }
};

watch(isOpen, (open) => {
    if (open) {
        statusMessage.value = "";
        loadEditors();
    }
});
</script>
