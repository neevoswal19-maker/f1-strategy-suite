import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// served from https://neevoswal19-maker.github.io/f1-strategy-suite/
export default defineConfig({
  base: '/f1-strategy-suite/',
  plugins: [react(), tailwindcss()],
})
