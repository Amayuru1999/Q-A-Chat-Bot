// vite.config.ts
import { defineConfig } from 'vite'
import { resolve } from 'node:path'   // or: import * as path from 'node:path'

export default defineConfig({
  server: { port: 5173, strictPort: true },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      // if using namespace import: '@': path.resolve(__dirname, './src'),
    },
  },
})