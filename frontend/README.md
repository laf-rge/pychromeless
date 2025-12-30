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
bun run test
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
- **Vitest** - Testing framework
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
│   ├── services/        # API and service integrations
│   ├── utils/          # Utility functions
│   └── test-utils/     # Testing utilities
├── public/             # Static assets
└── dist/              # Build output
```

## Deployment

The frontend is deployed to a Namecheap server via Terraform. See the main project README for deployment instructions.

## Notes

- This project uses **Bun** as the package manager. Use `bun` commands instead of `npm` or `yarn`.
- React 19 is used throughout the application.
- The lockfile is `bun.lockb` (not `package-lock.json` or `yarn.lock`).
