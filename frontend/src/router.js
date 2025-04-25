import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Result from './views/Result.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: {
      title: '明星脸测试 - 上传照片'
    }
  },
  {
    path: '/result/:id',
    name: 'Result',
    component: Result,
    meta: {
      title: '明星脸测试 - 对比结果'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局导航守卫，修改页面标题
router.beforeEach((to, from, next) => {
  document.title = to.meta.title || '明星脸相似度测试'
  next()
})

export default router