import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const api = ['/chat', '/candidaturas', '/health', '/react', '/memoria', '/sessoes', '/curriculo', '/modelos', '/modelo', '/avaliacao']

export default defineConfig({
  plugins: [vue()],
  build: { outDir: 'dist', emptyOutDir: true, chunkSizeWarningLimit: 900 },
  server: { proxy: Object.fromEntries(api.map((path) => [path, 'http://127.0.0.1:8000'])) },
})
