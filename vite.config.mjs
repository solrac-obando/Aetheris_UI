import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, 'wasm/adapters/aether_renderer.js'),
      name: 'AetherRenderer',
      fileName: 'aether-renderer',
      formats: ['es', 'umd'],
    },
    rollupOptions: {
      external: [],
      output: {
        globals: {},
        assetFileNames: 'aether-renderer.[ext]',
      },
    },
    target: 'es2020',
    minify: 'terser',
    sourcemap: false,
    chunkSizeWarningLimit: 500,
  },
  resolve: {
    alias: {},
  },
});