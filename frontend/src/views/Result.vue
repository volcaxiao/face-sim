<template>
  <div class="result-container">
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>
    
    <div v-else-if="error" class="error-container">
      <el-empty :description="error">
        <template #image>
          <el-icon style="font-size: 4rem; color: #909399;"><circle-close /></el-icon>
        </template>
        <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
      </el-empty>
    </div>
    
    <div v-else class="result-content">
      <h2 class="result-title">您的明星脸测试结果</h2>
      
      <div class="comparison-container">
        <div class="user-photo-container">
          <h3>您的照片</h3>
          <img :src="result.user_photo" class="user-photo" alt="用户照片" />
        </div>
        
        <el-divider direction="vertical">
          <el-icon><arrow-right /></el-icon>
        </el-divider>
        
        <div class="celebrities-container">
          <h3>最相似的明星</h3>
          <div class="celebrities-grid">
            <div v-for="(detail, index) in result.details" :key="index" class="celebrity-card">
              <el-card shadow="hover">
                <div class="celebrity-info">
                  <img :src="detail.celebrity.photo" class="celebrity-photo" :alt="detail.celebrity.name" />
                  <div class="celebrity-data">
                    <h4>{{ detail.celebrity.name }}</h4>
                    <div class="similarity">
                      <div class="similarity-value">{{ formatSimilarity(detail.similarity) }}%</div>
                      <el-progress 
                        :percentage="detail.similarity" 
                        :color="getSimilarityColor(detail.similarity)" 
                        :stroke-width="10" />
                    </div>
                    <div class="celebrity-description" v-if="detail.celebrity.description">
                      {{ truncateText(detail.celebrity.description, 50) }}
                    </div>
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </div>
      </div>
      
      <div class="actions">
        <el-button type="primary" @click="$router.push('/')">再来一次</el-button>
        <el-button type="success" @click="shareResult">分享结果</el-button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getComparisonResult } from '../services/api'
import { ElMessage } from 'element-plus'

export default {
  name: 'Result',
  setup() {
    const route = useRoute()
    const loading = ref(true)
    const error = ref('')
    const result = ref(null)
    
    const fetchResultData = async () => {
      const id = route.params.id
      if (!id) {
        error.value = '无效的结果ID'
        loading.value = false
        return
      }
      
      try {
        // 调用 API 获取真实结果数据，而不是使用模拟数据
        console.log('正在获取结果数据，ID:', id)
        const data = await getComparisonResult(id)
        console.log('API返回的结果数据:', data)
        
        if (!data || !data.details || data.details.length === 0) {
          error.value = '未找到比对结果，可能已过期或被删除'
          loading.value = false
          return
        }
        
        // 使用真实 API 返回的数据
        result.value = data
      } catch (err) {
        console.error('获取结果数据失败:', err)
        error.value = err.message || '获取结果数据失败，请稍后重试'
      } finally {
        loading.value = false
      }
    }
    
    const formatSimilarity = (value) => {
      return value ? value.toFixed(1) : '0'
    }
    
    const getSimilarityColor = (value) => {
      if (value > 80) return '#67C23A'
      if (value > 60) return '#409EFF'
      return '#E6A23C'
    }
    
    const truncateText = (text, length = 100) => {
      if (!text || text.length <= length) return text
      return text.substring(0, length) + '...'
    }
    
    const shareResult = () => {
      // 这里可以实现分享功能，如复制链接、生成图片等
      // 示例仅显示消息
      ElMessage({
        message: '分享功能开发中...',
        type: 'info'
      })
    }
    
    onMounted(() => {
      fetchResultData()
    })
    
    return {
      loading,
      error,
      result,
      formatSimilarity,
      getSimilarityColor,
      truncateText,
      shareResult
    }
  }
}
</script>

<style scoped>
.result-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 1rem;
}

.loading-container {
  padding: 2rem;
}

.error-container {
  padding: 3rem 0;
  text-align: center;
}

.result-title {
  text-align: center;
  margin-bottom: 2rem;
  color: #303133;
}

.comparison-container {
  display: flex;
  align-items: center;
  margin-bottom: 2rem;
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.user-photo-container {
  flex: 0 0 30%;
  text-align: center;
}

.user-photo {
  max-width: 100%;
  max-height: 250px;
  object-fit: contain;
  border-radius: 8px;
}

.celebrities-container {
  flex: 0 0 65%;
}

.celebrities-container h3,
.user-photo-container h3 {
  margin-bottom: 1rem;
  text-align: center;
  color: #409eff;
}

.celebrities-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.celebrity-card {
  margin-bottom: 1rem;
}

.celebrity-info {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.celebrity-photo {
  width: 100%;
  max-height: 180px;
  object-fit: cover;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.celebrity-data {
  width: 100%;
  text-align: center;
}

.celebrity-data h4 {
  margin-bottom: 0.5rem;
  color: #303133;
}

.similarity {
  margin: 0.5rem 0;
}

.similarity-value {
  text-align: right;
  margin-bottom: 0.25rem;
  font-weight: bold;
  color: #409eff;
}

.celebrity-description {
  font-size: 0.85rem;
  color: #606266;
  margin-top: 0.5rem;
  text-align: left;
}

.actions {
  text-align: center;
  margin-top: 1.5rem;
}

@media (max-width: 768px) {
  .comparison-container {
    flex-direction: column;
  }
  
  .user-photo-container {
    margin-bottom: 1.5rem;
    width: 100%;
  }
  
  .el-divider--vertical {
    height: 1px;
    width: 100%;
    margin: 1rem 0;
  }
  
  .celebrities-container {
    width: 100%;
  }
}
</style>