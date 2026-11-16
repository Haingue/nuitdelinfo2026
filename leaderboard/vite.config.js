import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/nuitdelinfo2026/',
  plugins: [react()],
  server: {
    allowedHosts: true
  }
})
