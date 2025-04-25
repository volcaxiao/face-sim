import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// 导入Element Plus图标
import * as ElementPlusIcons from '@element-plus/icons-vue'

const app = createApp(App)

// 全局注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIcons)) {
  app.component(key, component)
  // 同时添加i-前缀的别名，解决template中使用i-前缀的问题
  app.component(`i-${key.toLowerCase()}`, component)
}

app.use(router)
app.use(ElementPlus)
app.mount('#app')