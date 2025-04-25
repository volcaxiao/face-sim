const { defineConfig } = require('@vue/cli-service')
const webpack = require('webpack')

module.exports = defineConfig({
  transpileDependencies: true,
  // 关闭ESLint检查
  lintOnSave: false,
  // 部署应用包的基本URL
  publicPath: '/',
  // 生产环境构建文件的目录
  outputDir: 'dist',
  // 放置生成的静态资源的目录
  assetsDir: 'static',
  // 开发环境配置
  devServer: {
    port: 8080,
    // 添加WebSocket配置
    client: {
      webSocketURL: 'auto://0.0.0.0:0/ws',
      overlay: {
        errors: true,
        warnings: false
      }
    },
    // 允许所有IP访问，解决WebSocket连接问题
    allowedHosts: 'all',
    proxy: {
      '/api': {
        target: process.env.VUE_APP_API_URL || 'http://localhost:8000',
        changeOrigin: true
      },
      '/media': {
        target: process.env.VUE_APP_API_URL || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  // 配置Webpack
  configureWebpack: {
    // 提供一个可用于Vue模板内插值的对象
    performance: {
      hints: false
    },
    // 使用plugins数组添加DefinePlugin来设置特性标志
    plugins: [
      new webpack.DefinePlugin({
        __VUE_OPTIONS_API__: true,
        __VUE_PROD_DEVTOOLS__: false,
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false
      })
    ]
  }
})