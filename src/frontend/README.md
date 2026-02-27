# FlowKit Frontend

Modern Vue 3 + TypeScript frontend for FlowKit.

## Tech Stack

- **Vue 3** - Progressive JavaScript framework
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool
- **Pinia** - State management
- **Vue Router** - Client-side routing
- **ECharts** - Data visualization
- **Catppuccin** - Beautiful color scheme

## Project Structure

```
src/frontend/
├── src/
│   ├── api/              # API client modules
│   ├── assets/           # Static assets (styles, images)
│   ├── components/       # Reusable Vue components
│   │   ├── layout/       # Layout components (TitleBar, Toast)
│   │   └── common/       # Common UI components
│   ├── composables/      # Vue composables (hooks)
│   ├── stores/           # Pinia stores
│   ├── types/            # TypeScript type definitions
│   ├── utils/            # Utility functions
│   ├── views/            # Page components
│   │   ├── Launcher/     # Launcher view
│   │   ├── Dashboard/    # Dashboard view
│   │   ├── Overview/     # Token management
│   │   ├── FlowEditor/   # Flow editor
│   │   └── Settings/     # Settings view
│   ├── App.vue           # Root component
│   ├── main.ts           # Entry point
│   └── router.ts         # Route configuration
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## Development

### Install Dependencies

```bash
cd src/frontend
npm install
```

### Start Dev Server

```bash
npm run dev
```

The dev server will start at `http://localhost:5173` with API proxy to `http://127.0.0.1:18900`.

### Build for Production

```bash
npm run build
```

Output will be generated to `../web/static/`.

## Features

### Implemented

- ✅ **Launcher View** - Action grid with search and execution
- ✅ **Dashboard View** - Token statistics and usage trends
- ✅ **Overview View** - Token management (CRUD)
- ✅ **Flow Editor View** - Flow orchestration interface
- ✅ **Settings View** - Theme, window, hotkey, and API settings
- ✅ **Catppuccin Theme** - Mocha (dark) and Latte (light) themes
- ✅ **Smooth Animations** - Tab transitions, card hovers, toasts
- ✅ **Toast Notifications** - Success, error, warning, info
- ✅ **PyWebView Integration** - Window controls and native features
- ✅ **Type-Safe API Client** - Full TypeScript coverage
- ✅ **State Management** - Pinia stores for all views

### To Be Enhanced

- 🔨 **Action Editor Modal** - Full CRUD for actions
- 🔨 **Flow Canvas** - LiteGraph.js integration
- 🔨 **Context Menu** - Right-click actions
- 🔨 **Drag & Drop** - Action reordering
- 🔨 **Search Results** - Display search results
- 🔨 **Token Modals** - Add/Edit token forms
- 🔨 **Hotkey Recorder** - Record keyboard shortcuts

## API Integration

All API calls use the unified client in `src/api/index.ts`:

```typescript
import { api } from '@/api/index'

// GET request
const data = await api.get<ResponseType>('/endpoint')

// POST request
await api.post('/endpoint', { body })

// PUT request
await api.put('/endpoint', { body })

// DELETE request
await api.delete('/endpoint')
```

API responses follow the format:

```typescript
{
  code: 0,        // 0 = success
  data: T,        // Response data
  error: string   // Error message
}
```

## Styling

### Catppuccin Theme

The app uses Catppuccin color scheme with CSS variables:

```css
var(--base)      /* Background */
var(--surface0)  /* Card background */
var(--text)      /* Primary text */
var(--accent)    /* Accent color (mauve) */
var(--red)       /* Error color */
var(--green)     /* Success color */
/* ... and more */
```

Switch themes in Settings or programmatically:

```typescript
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
appStore.setTheme('latte') // or 'mocha'
```

### Animations

Predefined animations in `assets/styles/animations.css`:

- `tab-fade` - Tab transitions
- `toast` - Toast notifications
- `modal` - Modal dialogs
- `card-hover` - Card hover effects
- `drag-ghost` - Drag & drop

## State Management

Each view has its own Pinia store:

```typescript
// Launcher
import { useLauncherStore } from '@/stores/launcher'
const store = useLauncherStore()
await store.fetchActions()

// Dashboard
import { useDashboardStore } from '@/stores/dashboard'
const store = useDashboardStore()
await store.fetchStats()

// Overview
import { useOverviewStore } from '@/stores/overview'
const store = useOverviewStore()
await store.fetchTokens()

// Flow Editor
import { useFlowEditorStore } from '@/stores/flowEditor'
const store = useFlowEditorStore()
await store.fetchStepTypes()

// Settings
import { useSettingsStore } from '@/stores/settings'
const store = useSettingsStore()
await store.fetchConfig()
```

## Composables

Reusable logic via Vue composables:

```typescript
// Toast notifications
import { useToast } from '@/composables/useToast'
const { success, error, warning, info } = useToast()
success('Operation completed!')

// PyWebView integration
import { usePyWebView } from '@/composables/usePyWebView'
const { isPyWebView, minimizeWindow, closeWindow } = usePyWebView()
```

## Build Configuration

### Vite Config

- **Output**: `../web/static/`
- **Dev Proxy**: `/api` → `http://127.0.0.1:18900`
- **Code Splitting**:
  - `vendor` - Vue, Pinia, Vue Router, VueUse
  - `echarts` - ECharts library
  - `litegraph` - LiteGraph.js library

### TypeScript Config

- **Target**: ES2020
- **Module**: ESNext
- **Strict Mode**: Enabled
- **Path Alias**: `@/*` → `./src/*`

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## License

Same as FlowKit main project.
