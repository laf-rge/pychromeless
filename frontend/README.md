# WMC Frontend

React 19 frontend application for Wagoner Management Corp, built with Vite, Tailwind CSS, and Bun.

## Prerequisites

- [Bun](https://bun.sh) >= 1.0.0
- Node.js 18+ (for compatibility, though Bun is the primary package manager)

## Getting Started

### Install Dependencies

```bash
bun install
```

### Development

```bash
bun run dev
```

The application will be available at `http://localhost:5173`

### Build

```bash
bun run build
```

### Test

```bash
# Unit tests (Vitest)
bun run test

# E2E tests (Playwright)
bun run test:e2e           # Headless
bun run test:e2e:ui        # With Playwright UI
bun run test:e2e:headed    # With visible browser
```

### Lint

```bash
bun run lint
```

## Technology Stack

- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite 7** - Build tool and dev server
- **Tailwind CSS 4** - Utility-first CSS framework
- **Headless UI** - Unstyled, accessible UI components
- **Radix UI** - Accessible component primitives
- **React Router** - Client-side routing
- **MSAL (Microsoft Authentication Library)** - Azure AD authentication
- **Vitest** - Unit testing framework
- **Playwright** - E2E testing framework
- **Bun** - Package manager and runtime

## Project Structure

```
frontend/
├── src/
│   ├── components/     # React components
│   │   ├── ui/         # Base UI components
│   │   ├── layout/     # Layout components
│   │   └── features/   # Feature-specific components
│   ├── pages/          # Page components
│   ├── services/       # API and service integrations
│   ├── stores/         # Zustand state stores
│   ├── utils/          # Utility functions
│   └── test-utils/     # Testing utilities (mock providers, helpers)
├── e2e/                # Playwright E2E tests
├── public/             # Static assets
└── dist/               # Build output
```

## E2E Testing

E2E tests use Playwright and run with mocked authentication:

- **Test mode**: Set via `VITE_E2E_MODE=true` (Playwright config does this automatically)
- **Mock auth**: `src/test-utils/MockMsalProvider.tsx` provides mock MSAL context
- **Test routes**: `src/routes.test.tsx` provides auth-free routes for testing
- **Test files**: Located in `e2e/` directory

When `VITE_E2E_MODE=true`:
1. App uses `MockMsalProvider` instead of real MSAL
2. All routes are accessible without authentication
3. API calls can be mocked via Playwright's `page.route()`

## Deployment

The frontend is deployed to a Namecheap server via `make frontend-deploy` (direct rsync). Credentials are stored in AWS SSM Parameter Store.

## Notes

- This project uses **Bun** as the package manager. Use `bun` commands instead of `npm` or `yarn`.
- React 19 is used throughout the application.
- The lockfile is `bun.lockb` (not `package-lock.json` or `yarn.lock`).
