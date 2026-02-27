import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: Object.fromEntries(
      [
        '/floorplan',
        '/zone',
        '/warehouse',
        '/status',
        '/register',
        '/login',
        '/manifest',
        '/inventory',
        '/expiries',
        '/start',
        '/stop',
        '/share-item',
        '/import-inventory',
        '/uploads',
      ].map((route) => [route, { target: 'http://localhost:8002', changeOrigin: true }])
    ),
  },
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: './src/__tests__/setup.js',
  },
})
