/// <reference types="bun-types" />

interface ImportMetaEnv {
  readonly DEV: boolean;
  readonly PROD: boolean;
  readonly MODE: string;
  readonly BUN_E2E_MODE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
