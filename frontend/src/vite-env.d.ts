/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Optional absolute backend URL, e.g. https://api.example.com (leave empty in dev: Vite proxies /api). */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
