<template>
    <UTooltip :text="tooltipText" :popper="{ placement: 'bottom' }">
        <div class="flex items-center gap-2 pl-2 pr-3 py-1 rounded-lg bg-primary select-none">
            <UIcon name="i-heroicons-user-circle" class="text-2xl text-white flex-shrink-0" />
            <div class="leading-none">
                <div class="text-sm font-medium text-white">{{ nameLine }}</div>
                <div v-if="isAuthenticated" class="text-[10px] text-white/70 mt-0.5">{{ roleLabel }}</div>
            </div>
        </div>
    </UTooltip>
</template>

<script setup lang="ts">
const { isAuthenticated, user, role } = useAuth();

const roleLabel = computed(() => role.value.charAt(0).toUpperCase() + role.value.slice(1));

const displayName = computed(() => {
    if (user.value?.auth_disabled) return undefined;
    if (user.value?.given_name && user.value?.family_name) {
        return `${user.value.given_name} ${user.value.family_name}`;
    }
    return user.value?.preferred_username;
});

const nameLine = computed(() => {
    if (!isAuthenticated.value) return "Not signed in";
    return displayName.value || roleLabel.value;
});

const tooltipText = computed(() => {
    if (!isAuthenticated.value) return "You are not recognized -- sign in to get viewer access.";
    const base =
        role.value === "admin"
            ? "You are an admin: full access, plus managing editors."
            : role.value === "editor"
              ? "You are an editor: you can create, edit, and delete entries."
              : "You are a viewer: read-only access.";
    return user.value?.auth_disabled ? `${base} (Authentication is disabled in this environment.)` : base;
});
</script>
