// NOTE: happy-dom MUST be registered via happy-dom-register.ts preload FIRST
// This file assumes DOM globals (window, document) already exist

import { expect } from "bun:test";
import * as matchers from "@testing-library/jest-dom/matchers";
import { configure } from "@testing-library/react";

// Configure testing-library to use real timers and longer timeout
// This prevents conflicts with Bun's fake timer implementation
configure({
  // Use a longer timeout for async operations
  asyncUtilTimeout: 5000,
  // Don't throw on multiple elements - just warn
  throwSuggestions: false,
});

// Extend Bun's expect with jest-dom matchers
expect.extend(matchers);

// Mock window.matchMedia (used by some UI components)
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {},
  }),
});
