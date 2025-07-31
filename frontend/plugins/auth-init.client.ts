/**
 * Initialize authentication system on client-side
 * This plugin ensures that the enhanced API client with token refresh is properly set up
 */
export default defineNuxtPlugin(() => {
  // Initialize the enhanced API client
  // This triggers the setup of interceptors and automatic token refresh
  const { baseUrl } = useApiClient()
  
  // Check authentication status on app start
  const { checkAuthStatus } = useAuth()
  
  // Perform initial auth check without blocking the app
  checkAuthStatus().catch((error) => {
    console.warn('Initial auth check failed:', error)
    // Don't throw - this is expected if the user is not authenticated
  })
  
  console.debug('Auth system initialized with automatic token refresh')
})
