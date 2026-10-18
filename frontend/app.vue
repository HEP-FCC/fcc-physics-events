<template>
    <UApp class="min-h-screen flex flex-col">
        <!-- Skip to main content link for accessibility -->
        <a href="#main-content" class="skip-link">Skip to main content</a>

        <!-- Navigation Header -->
        <header class="bg-space-50 border-space-200">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <!-- Mobile Layout (responsive stacked) -->
                <div class="flex flex-col py-2 sm:hidden">
                    <!-- First row: Logo, Title, About (icon), and Auth -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3 flex-1 min-w-0">
                            <NuxtLink to="/" class="flex items-center flex-shrink-0" @click="handleLogoClick">
                                <NuxtImg src="/logo.png" :alt="appTitle" class="h-8 w-auto" />
                            </NuxtLink>
                            <h1 class="text-lg font-semibold font-sans truncate select-none">
                                {{ appTitle }}
                            </h1>
                        </div>
                        <div class="flex items-center gap-2 flex-shrink-0">
                            <!-- User Management Modal - Icon only on mobile, admins only -->
                            <UserManagementModal v-if="isAdmin" icon-only />
                            <!-- Edit Modal - Icon only on mobile, editors and admins only -->
                            <EditModal v-if="canEdit" icon-only />
                            <!-- About Modal - Icon only on mobile -->
                            <AboutModal icon-only />
                            <!-- Role badge - also the account dropdown trigger (sign in/out, user area). Always rightmost. -->
                            <UserRoleBadge />
                        </div>
                    </div>
                </div>

                <!-- Desktop Layout (single row) -->
                <div class="hidden sm:flex items-center h-16">
                    <!-- Left: Logo -->
                    <div class="flex items-center">
                        <NuxtLink class="flex items-center cursor-pointer" @click="handleLogoClick">
                            <NuxtImg src="/logo.png" :alt="appTitle" class="h-8 w-auto" />
                        </NuxtLink>
                    </div>

                    <!-- Center: App Title -->
                    <h1 class="px-5 text-xl font-semibold font-sans whitespace-nowrap select-none">
                        {{ appTitle }}
                    </h1>
                    <!-- Right: Users, Edit, About, and role badge/account dropdown (always rightmost) -->
                    <div class="ml-auto flex items-center space-x-4">
                        <UserManagementModal v-if="isAdmin" />
                        <EditModal v-if="canEdit" />
                        <AboutModal />
                        <UserRoleBadge />
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main id="main-content" class="flex-1">
            <NuxtPage />
        </main>
    </UApp>
</template>

<script setup lang="ts">
import AboutModal from "~/components/AboutModal.vue";
import EditModal from "~/components/EditModal.vue";
import UserManagementModal from "~/components/UserManagementModal.vue";
import UserRoleBadge from "~/components/UserRoleBadge.vue";

// Check authentication status on app initialization
const { checkAuthStatus, hasRole } = useAuth();
const { initializeNavigation } = useDynamicNavigation();
const { appTitle } = useAppConfiguration();
const router = useRouter();

const canEdit = computed(() => hasRole("editor"));
const isAdmin = computed(() => hasRole("admin"));

const handleLogoClick = async (event: Event) => {
    // Prevent the default link navigation
    event.preventDefault();

    // Try to use global search controller first
    const { clearSearchAndRefresh, hasController } = useGlobalSearchControl();

    if (hasController.value) {
        // Use the global search controller to clear search and refresh
        await clearSearchAndRefresh();
        // Navigate to home page
        await router.push({ path: "/" });
    } else {
        // Fallback to route-based navigation if no controller is available
        await router.push({ path: "/", query: { q: "" } });
    }
};

onMounted(async () => {
    // Initialize navigation configuration globally
    await initializeNavigation();

    // Check authentication status
    await checkAuthStatus();
});
</script>

<!--
Powered by friendship!
                                                    /
                                                  .7
                                       \       , //
                                       |\.--._/|//
                                      /\ ) ) ).'/
                                     /(  \  // /
                                    /(   J`((_/ \
                                   / ) | _\     /
                                  /|)  \  eJ    L
                                 |  \ L \   L   L
                                /  \  J  `. J   L
                                |  )   L   \/   \
                               /  \    J   (\   /
             _....___         |  \      \   \```
      ,.._.-'        '''--...-||\     -. \   \
    .'.=.'                    `         `.\ [ Y
   /   /                                  \]  J
  Y / Y                                    Y   L
  | | |          \                         |   L
  | | |           Y                        A  J
  |   I           |                       /I\ /
  |    \          I             \        ( |]/|
  J     \         /._           /        -tI/ |
   L     )       /   /'-------'J           `'-:.
   J   .'      ,'  ,' ,     \   `'-.__          \
    \ T      ,'  ,'   )\    /|        ';'---7   /
     \|    ,'L  Y...-' / _.' /         \   /   /
      J   Y  |  J    .'-'   /         ,--.(   /
       L  |  J   L -'     .'         /  |    /\
       |  J.  L  J     .-;.-/       |    \ .' /
       J   L`-J   L____,.-'`        |  _.-'   |
        L  J   L  J                  ``  J    |
        J   L  |   L                     J    |
         L  J  L    \                    L    \
         |   L  ) _.'\                    ) _.'\
         L    \('`    \                  ('`    \
          ) _.'\`-....'                   `-....'
         ('`    \
          `-.___/   sk
 -->
