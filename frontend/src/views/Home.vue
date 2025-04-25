<template>
  <div class="home-container">
    <el-card class="upload-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <h2>上传一张照片，看看你像哪位明星</h2>
        </div>
      </template>
      
      <div class="upload-area">
        <el-upload
          class="upload"
          drag
          :auto-upload="false"
          :show-file-list="false"
          accept="image/jpeg,image/png,image/jpg"
          :on-change="handleFileChange"
          :multiple="false"
        >
          <div v-if="!imageUrl" class="upload-content">
            <el-icon class="el-icon--upload"><i-upload /></el-icon>
            <div class="el-upload__text">
              点击或拖拽图片至此处上传
              <div class="el-upload__tip">
                支持JPG、PNG格式图片，建议选择有正脸的照片
              </div>
            </div>
          </div>
          <img v-else :src="imageUrl" class="preview-image" />
        </el-upload>
        
        <!-- 照片质量提示 -->
        <div v-if="imageUrl" class="photo-tips">
          <el-alert
            title="提高匹配准确性的建议"
            type="info"
            :closable="false"
            show-icon
          >
            <div class="tips-content">
              <div class="tip-item">✓ 确保面部清晰且光线充足</div>
              <div class="tip-item">✓ 正面面孔效果最佳</div>
              <div class="tip-item">✓ 避免过度修饰或美颜滤镜</div>
            </div>
          </el-alert>
        </div>
        
        <div class="buttons-area">
          <el-button v-if="imageFile" @click="resetImage" size="large">重新选择</el-button>
          <el-button v-if="imageFile" type="primary" @click="submitImage" size="large" :loading="uploading">
            {{ uploading ? '处理中...' : '开始分析' }}
          </el-button>
        </div>
        
        <!-- 处理进度显示 -->
        <div v-if="processing" class="progress-area">
          <div class="progress-info">
            <span class="status-text">{{ processingStatusText }}</span>
            <span class="progress-percentage">{{ progress }}%</span>
          </div>
          <el-progress 
            :percentage="progress" 
            :status="progressStatus"
            :stroke-width="14"
            :show-text="false"
            :color="getProgressColor(progress)"
          ></el-progress>
          <div class="progress-detail">{{ progressDetail }}</div>
        </div>
        
        <!-- 添加错误信息展示区域 -->
        <div v-if="errorMsg" class="error-message">
          <el-alert
            :title="errorMsg"
            type="error"
            :closable="true"
            show-icon
            @close="clearError"
          >
          </el-alert>
        </div>
      </div>
    </el-card>
    
    <!-- 历史记录区域 -->
    <el-collapse v-if="hasHistory" class="history-collapse">
      <el-collapse-item title="历史比对记录" name="1">
        <div class="history-controls" v-if="historyItems.length > 0">
          <el-button type="text" @click="refreshHistory">
            <el-icon><refresh /></el-icon> 刷新记录
          </el-button>
          <el-button type="text" @click="clearHistory" v-if="historyItems.length > 0">
            <el-icon><delete /></el-icon> 清空历史
          </el-button>
        </div>
        <el-empty v-if="historyItems.length === 0" description="暂无历史记录"></el-empty>
        <div v-else class="history-list">
          <el-card v-for="item in historyItems" :key="item.id" class="history-item" shadow="hover">
            <div class="history-item-content" @click="goToResult(item.id)">
              <div class="history-image">
                <img v-if="item.user_photo_url" :src="item.user_photo_url" alt="历史照片" />
                <el-icon v-else><picture /></el-icon>
              </div>
              <div class="history-info">
                <div class="history-date">{{ formatDate(item.created_at) }}</div>
                <div class="history-status" :class="item.processing_status">
                  {{ getStatusText(item.processing_status) }}
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </el-collapse-item>
    </el-collapse>
    
    <el-divider>
      <span class="divider-content">明星脸相似度测试是如何工作的?</span>
    </el-divider>
    
    <div class="how-it-works">
      <div class="step-card">
        <div class="step-number">1</div>
        <h3>上传照片</h3>
        <p>选择您的照片上传，照片清晰且有正面面部效果较好</p>
      </div>
      <div class="step-card">
        <div class="step-number">2</div>
        <h3>AI分析</h3>
        <p>系统将使用Face++人工智能分析您的面部特征</p>
      </div>
      <div class="step-card">
        <div class="step-number">3</div>
        <h3>查看结果</h3>
        <p>系统将返回与您最相似的三位明星及相似度分析</p>
      </div>
    </div>
    
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { uploadPhoto, getComparisonStatus, getComparisonHistory } from '../services/api'

export default {
  name: 'Home',
  setup() {
    const router = useRouter()
    const imageFile = ref(null)
    const imageUrl = ref('')
    const uploading = ref(false)
    const errorMsg = ref('')
    const processing = ref(false)
    const processingId = ref(null)
    const progress = ref(0)
    const processingStatus = ref('')
    const progressTimer = ref(null)
    const historyItems = ref([])
    const failedAttempts = ref(0)
    
    // 计算处理状态文本
    const processingStatusText = computed(() => {
      switch (processingStatus.value) {
        case 'processing':
          if (progress.value < 10) return '正在上传照片...'
          if (progress.value < 30) return '正在检测人脸...'
          if (progress.value < 90) return '正在比对相似度...'
          return '处理即将完成...'
        case 'completed':
          return '处理完成'
        case 'failed':
          return '处理失败'
        default:
          return '正在处理...'
      }
    })
    
    // 计算进度条状态样式
    const progressStatus = computed(() => {
      if (processingStatus.value === 'completed') return 'success'
      if (processingStatus.value === 'failed') return 'exception'
      return ''
    })
    
    // 获取渐变进度条颜色
    const getProgressColor = (percentage) => {
      if (percentage < 30) return '#909399'  // 灰色
      if (percentage < 60) return '#e6a23c'  // 黄色
      if (percentage < 90) return '#409eff'  // 蓝色
      return '#67c23a'  // 绿色
    }
    
    // 进度详情描述
    const progressDetail = computed(() => {
      switch (processingStatus.value) {
        case 'processing':
          if (progress.value < 10) return '正在准备您的照片并上传到服务器'
          if (progress.value < 30) return '正在使用AI识别您的照片中的人脸'
          if (progress.value < 90) return '正在与数据库中的明星进行匹配比对'
          return '正在生成最终的比对结果'
        case 'completed':
          return '比对完成，正在跳转到结果页面'
        case 'failed':
          return '处理失败，请检查您的照片后重试'
        default:
          return ''
      }
    })
    
    // 是否显示历史记录区域
    const hasHistory = computed(() => {
      return historyItems.value.length > 0 || localStorage.getItem('face_session_id')
    })
    
    // 格式化日期
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      const now = new Date()
      const diff = Math.floor((now - date) / 1000)
      
      if (diff < 60) return '刚刚'
      if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
      if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
      if (date.getFullYear() === now.getFullYear()) {
        return `${date.getMonth() + 1}月${date.getDate()}日 ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
      }
      return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
    }
    
    // 获取状态文本
    const getStatusText = (status) => {
      switch (status) {
        case 'processing': return '处理中'
        case 'completed': return '已完成'
        case 'failed': return '失败'
        default: return '未知'
      }
    }
    
    // 加载历史记录
    const loadHistory = async () => {
      try {
        const history = await getComparisonHistory()
        historyItems.value = history || []
      } catch (error) {
        console.error('加载历史记录失败:', error)
      }
    }
    
    // 刷新历史记录
    const refreshHistory = async () => {
      try {
        await loadHistory()
        ElMessage({
          message: '历史记录已刷新',
          type: 'success',
          duration: 2000
        })
      } catch (error) {
        console.error('刷新历史记录失败:', error)
        ElMessage.error('刷新历史记录失败')
      }
    }
    
    // 清空历史记录
    const clearHistory = () => {
      ElMessageBox.confirm('确定要清空所有历史记录吗？此操作不可撤销', '确认清空', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        // 这里只是前端清空，实际项目中可能需要调用后端API
        historyItems.value = []
        localStorage.removeItem('face_session_id')
        ElMessage({
          type: 'success',
          message: '历史记录已清空'
        })
      }).catch(() => {
        // 用户取消清空操作
      })
    }
    
    // 跳转到结果页面
    const goToResult = (id) => {
      router.push(`/result/${id}`)
    }
    
    const handleFileChange = (file) => {
      if (!file || !file.raw) {
        ElMessage.error('图片上传失败，请重试')
        return
      }
      
      const isJpgOrPng = file.raw.type === 'image/jpeg' || file.raw.type === 'image/png'
      const isLt5M = file.raw.size / 1024 / 1024 < 5
      
      if (!isJpgOrPng) {
        ElMessage.error('只支持JPG/PNG格式的图片！')
        return
      }
      if (!isLt5M) {
        ElMessage.error('图片大小不能超过5MB！')
        return
      }
      
      // 清除之前的错误信息
      clearError()
      
      imageFile.value = file.raw
      imageUrl.value = URL.createObjectURL(file.raw)
    }
    
    const resetImage = () => {
      imageFile.value = null
      imageUrl.value = ''
      clearError()
    }
    
    const clearError = () => {
      errorMsg.value = ''
    }
    
    // 轮询检查处理状态
    const checkProcessingStatus = async () => {
      if (!processingId.value) return
      
      try {
        const statusData = await getComparisonStatus(processingId.value)
        
        if (statusData) {
          processingStatus.value = statusData.status
          progress.value = statusData.progress || 0
          
          if (statusData.status === 'completed') {
            clearInterval(progressTimer.value)
            setTimeout(() => {
              router.push(`/result/${processingId.value}`)
            }, 1000)
          } else if (statusData.status === 'failed') {
            clearInterval(progressTimer.value)
            // 检查是否有错误信息
            errorMsg.value = statusData.message || statusData.error || '处理失败，请尝试上传不同的照片'
            processing.value = false
          }
        }
      } catch (error) {
        console.error('获取处理状态失败:', error)
        
        // 如果连续失败多次，才停止轮询并显示错误
        failedAttempts.value++
        
        if (failedAttempts.value >= 3) {
          clearInterval(progressTimer.value)
          errorMsg.value = error.message || '无法获取处理状态，请刷新页面重试'
          processing.value = false
        }
      }
    }
    
    // 开始处理状态轮询
    const startProcessingPolling = () => {
      // 清除之前可能存在的轮询
      if (progressTimer.value) {
        clearInterval(progressTimer.value)
      }
      
      // 设置初始状态
      processing.value = true
      processingStatus.value = 'processing'
      progress.value = 0
      
      // 开始轮询
      progressTimer.value = setInterval(checkProcessingStatus, 2000)
    }
    
    const submitImage = async () => {
      if (!imageFile.value) {
        ElMessage.warning('请先选择一张照片')
        return
      }
      
      uploading.value = true
      clearError()
      
      try {
        const result = await uploadPhoto(imageFile.value)
        console.log('上传照片结果:', result)
        
        if (result && result.id) {
          // 保存处理ID，开始轮询处理状态
          processingId.value = result.id
          uploading.value = false
          startProcessingPolling()
          
          // 添加到历史记录
          loadHistory()
        } else {
          console.error('服务器响应格式不正确:', result)
          errorMsg.value = '处理成功但响应格式不正确，请联系管理员'
          uploading.value = false
        }
      } catch (error) {
        console.error('上传照片失败详情:', error)
        
        if (error.message) {
          errorMsg.value = error.message
        } else {
          errorMsg.value = '上传照片失败，请重试'
        }
        
        let messageType = 'error'
        if (error.status === 400) {
          messageType = 'warning'
        } else if (error.status === 404) {
          messageType = 'info'
        }
        
        ElMessage({
          message: errorMsg.value,
          type: messageType,
          duration: 5000,
          showClose: true
        })
        
        uploading.value = false
      }
    }
    
    // 组件卸载时清理轮询
    onMounted(() => {
      loadHistory()
    })
    
    onBeforeUnmount(() => {
      if (progressTimer.value) {
        clearInterval(progressTimer.value)
      }
    })
    
    return {
      imageFile,
      imageUrl,
      uploading,
      errorMsg,
      processing,
      progress,
      processingStatusText,
      progressStatus,
      progressDetail,
      historyItems,
      hasHistory,
      handleFileChange,
      resetImage,
      clearError,
      submitImage,
      formatDate,
      getStatusText,
      goToResult,
      getProgressColor,
      refreshHistory,
      clearHistory
    }
  }
}
</script>

<style scoped>
.home-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 900px;
  margin: 0 auto;
  padding: 1rem;
}

.upload-card {
  width: 100%;
  margin-bottom: 2rem;
}

.card-header {
  text-align: center;
}

.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
}

.upload {
  width: 100%;
  max-width: 500px;
}

.upload-content {
  padding: 3rem 0;
}

.el-icon--upload {
  font-size: 3rem;
  color: #409eff;
  margin-bottom: 1rem;
}

.el-upload__tip {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #909399;
}

.preview-image {
  max-width: 100%;
  max-height: 300px;
  object-fit: contain;
  margin: 1rem 0;
}

.buttons-area {
  margin-top: 1rem;
  display: flex;
  justify-content: center;
  gap: 1rem;
}

/* 进度条区域样式 */
.progress-area {
  width: 100%;
  max-width: 500px;
  margin-top: 1.5rem;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.status-text {
  font-weight: bold;
  color: #409eff;
}

.progress-percentage {
  color: #606266;
}

.progress-detail {
  margin-top: 0.5rem;
  font-size: 0.9rem;
  color: #909399;
  text-align: center;
}

/* 错误信息样式 */
.error-message {
  width: 100%;
  max-width: 500px;
  margin-top: 1rem;
}

/* 照片质量提示样式 */
.photo-tips {
  width: 100%;
  max-width: 500px;
  margin-top: 1rem;
}

.tips-content {
  padding: 0.5rem 0;
}

.tip-item {
  margin: 0.35rem 0;
  font-size: 0.9rem;
}

/* 历史记录区域样式 */
.history-collapse {
  width: 100%;
  margin-bottom: 1.5rem;
}

.history-controls {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem;
  gap: 1rem;
}

.history-list {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.history-item {
  width: calc(33.33% - 1rem);
  min-width: 200px;
  cursor: pointer;
}

.history-item-content {
  display: flex;
  align-items: center;
}

.history-image {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  overflow: hidden;
  margin-right: 1rem;
  background-color: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.history-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.history-image .el-icon {
  font-size: 24px;
  color: #909399;
}

.history-info {
  flex: 1;
}

.history-date {
  font-size: 0.85rem;
  color: #606266;
  margin-bottom: 0.25rem;
}

.history-status {
  font-size: 0.75rem;
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
}

.history-status.completed {
  background-color: #f0f9eb;
  color: #67c23a;
}

.history-status.processing {
  background-color: #ecf5ff;
  color: #409eff;
}

.history-status.failed {
  background-color: #fef0f0;
  color: #f56c6c;
}

.divider-content {
  color: #606266;
  font-size: 1rem;
}

.how-it-works {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  width: 100%;
  margin-top: 1rem;
  gap: 1rem;
}

.step-card {
  flex: 1;
  min-width: 200px;
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  text-align: center;
  position: relative;
}

.step-number {
  position: absolute;
  top: -15px;
  left: 50%;
  transform: translateX(-50%);
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.step-card h3 {
  margin-top: 0.5rem;
  margin-bottom: 1rem;
  color: #409eff;
}

@media (max-width: 768px) {
  .how-it-works {
    flex-direction: column;
  }
  
  .step-card {
    margin-bottom: 2rem;
  }
  
  .history-item {
    width: 100%;
  }
}

/* 进度条颜色效果 */
:deep(.el-progress-bar__inner) {
  transition: all 0.3s ease;
}
</style>