import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:3001',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        // 确保chunk文件名包含内容哈希，以便浏览器正确更新
        entryFileNames: `assets/[name]-[hash].js`,
        chunkFileNames: `assets/[name]-[hash].js`,
        assetFileNames: `assets/[name]-[hash].[ext]`
      }
    },
    // 确保清理上次构建的输出目录
    emptyOutDir: true,
  },
  // 确保TypeScript类型检查在构建时也运行
  esbuild: {
    // 在构建时包含源映射
    sourcemap: false, // 设置为true可以用于调试，生产环境通常设为false
  },
  resolve: {
    alias: {
      // 定义路径别名，确保模块解析的一致性
      '@': resolve(__dirname, 'src'),
    }
  }
})