import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev server proxies /api -> FastAPI backend so the browser has no CORS issues
// and the frontend code can call same-origin `/api/...` paths.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5175,
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
      // Textbook figure images are served by the backend at /textbook-assets.
      // They are referenced by absolute path in <img src>, so the dev server
      // must forward them too (no rewrite — the backend mount path matches).
      '/textbook-assets': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
