import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    // 若需要代理后端，请在此处配置 proxy
    // proxy: { '/api': 'http://localhost:8000' }
  }
})
