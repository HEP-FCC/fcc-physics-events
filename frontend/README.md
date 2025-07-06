# FCC Physics Events Frontend

A Vue.js 3 / Nuxt.js 3 application for browsing and searching FCC physics datasets. This application provides an intuitive interface for physicists to explore datasets with advanced filtering, sorting, and metadata viewing capabilities.

## Features

- **Advanced Search**: Query datasets using GCLQL (Graph-based Context-aware Library Query Language)
- **Smart Filtering**: Filter by accelerator, campaign, detector, and stage
- **Flexible Viewing**: Toggle between infinite scroll and paginated modes
- **Bulk Operations**: Select multiple datasets for download
- **Metadata Exploration**: Expandable metadata view for detailed dataset information
- **Responsive Design**: Works on desktop and mobile devices

## Technology Stack

- **Nuxt.js 3**: Full-stack framework built on Vue.js 3
- **TypeScript**: Type-safe development
- **Nuxt UI**: Modern component library with Tailwind CSS
- **Composables**: Reusable business logic with Vue's Composition API

## Setup

Make sure to install dependencies:

```bash
# yarn (recommended)
yarn install

# npm
npm install

# pnpm
pnpm install
```

## Development Server

Start the development server on `http://localhost:3000`:

```bash
# yarn (recommended)
yarn dev

# npm
npm run dev

# pnpm
pnpm dev
```

## Production

Build the application for production:

```bash
# yarn
yarn build

# npm
npm run build

# pnpm
pnpm build
```

Locally preview production build:

```bash
# yarn
yarn preview

# npm
npm run preview

# pnpm
pnpm preview
```

## Project Structure

```
├── components/          # Vue components
│   ├── DatasetCard.vue             # Individual dataset display
│   ├── DatasetControls.vue         # Bulk operations and sorting
│   ├── DatasetList.vue             # Dataset listing container
│   ├── DatasetSearchInterface.vue  # Main search interface
│   ├── Metadata.vue                # Dataset metadata display
│   ├── NavigationMenu.vue          # Filter navigation
│   ├── ResultsSummary.vue          # Results count and pagination
│   └── SearchControls.vue          # Search input and permalink
├── composables/         # Reusable business logic
│   ├── getApiClient.ts             # API communication
│   ├── useDatasetSearch.ts         # Search functionality
│   ├── useDatasetSelection.ts      # Selection state management
│   └── useNavigationConfig.ts     # Filter configuration
├── pages/              # Application routes
├── types/              # TypeScript type definitions
└── assets/             # Static assets and global styles
```

## For Maintainers

This codebase follows Vue.js 3 and Nuxt.js 3 best practices:

- **Composables**: Business logic is extracted into reusable composables
- **TypeScript**: All components and functions are fully typed
- **Component Props**: Clear interfaces define component inputs and outputs
- **Error Handling**: Consistent error handling patterns throughout
- **Code Organization**: Related functionality is grouped together

### Common Tasks

**Adding a new filter option:**
1. Update the API client in `composables/getApiClient.ts`
2. Add the filter to `composables/useNavigationConfig.ts`
3. Update the navigation component if needed

**Modifying search behavior:**
1. Main search logic is in `composables/useDatasetSearch.ts`
2. UI controls are in `components/SearchControls.vue`

**Changing dataset display:**
1. Individual cards: `components/DatasetCard.vue`
2. Metadata display: `components/Metadata.vue`
3. List container: `components/DatasetList.vue`

## API Configuration

Configure the backend API URL in `nuxt.config.ts`:

```typescript
runtimeConfig: {
  public: {
    apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8000'
  }
}
```

Check out the [deployment documentation](https://nuxt.com/docs/getting-started/deployment) for more information.
