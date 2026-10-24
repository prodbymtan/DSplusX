import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The dev server forwards /api and /ws to FastAPI, so the browser only ever
// talks to one origin (no CORS, no "localhost on a phone" problems).
// 127.0.0.1 instead of localhost: Node can resolve localhost to IPv6 (::1)
// while uvicorn listens on IPv4, which causes confusing "connection refused" errors.
const backend = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: backend, changeOrigin: true },
      '/ws': { target: backend.replace(/^http/, 'ws'), ws: true },
    },
  },
  preview: {
    port: 4173,
    proxy: {
      '/api': { target: backend, changeOrigin: true },
      '/ws': { target: backend.replace(/^http/, 'ws'), ws: true },
    },
  },
})
