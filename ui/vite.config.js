import { defineConfig } from 'vite';

export default defineConfig({
  esbuild: { jsxFactory: 'host.h', jsxFragment: 'host.React.Fragment' },
  build: {
    outDir: 'dist',
    lib: { entry: 'src/plugin.jsx', formats: ['es'], fileName: () => 'remote-host-terminal.js' },
    rollupOptions: { external: ['react', 'react-dom'] },
  },
});
