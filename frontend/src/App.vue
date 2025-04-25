<template>
  <div class="app-container">
    <header class="app-header">
      <h1 @click="$router.push('/')" style="cursor: pointer;">明星脸相似度测试</h1>
    </header>
    <main class="main-content">
      <router-view></router-view>
    </main>
    <footer class="app-footer">
      <p>© {{ new Date().getFullYear() }} 明星脸相似度测试 | 基于Face++人脸识别技术</p>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Arial, sans-serif;
  background-color: #f5f7fa;
  color: #333;
}

.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  background-color: #409eff;
  color: white;
  padding: 1rem;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.main-content {
  flex: 1;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.app-footer {
  background-color: #f5f7fa;
  border-top: 1px solid #e4e7ed;
  padding: 1rem;
  text-align: center;
  color: #909399;
}
</style>