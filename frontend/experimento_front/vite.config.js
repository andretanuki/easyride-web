import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Porta 3000 fixa: o backend (django-cors-headers) já libera
// http://localhost:3000 em CORS_ALLOWED_ORIGINS por padrão.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    strictPort: true,
  },
});
