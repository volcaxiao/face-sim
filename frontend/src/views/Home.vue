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
        
        <div class="buttons-area">
          <el-button v-if="imageFile" @click="resetImage" size="large">重新选择</el-button>
          <el-button v-if="imageFile" type="primary" @click="submitImage" size="large" :loading="uploading">
            {{ uploading ? '处理中...' : '开始分析' }}
          </el-button>
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
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadPhoto } from '../services/api'

export default {
  name: 'Home',
  setup() {
    const imageFile = ref(null)
    const imageUrl = ref('')
    const uploading = ref(false)
    const errorMsg = ref('') // 新增错误信息状态
    
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
    
    const submitImage = async () => {
      if (!imageFile.value) {
        ElMessage.warning('请先选择一张照片')
        return
      }
      
      uploading.value = true
      clearError() // 清除之前可能存在的错误
      
      try {
        const result = await uploadPhoto(imageFile.value)
        console.log('上传照片结果:', result) // 添加日志，查看实际响应
        
        if (result && result.id) {
          // 修正导航URL格式，确保正确处理根路径
          const baseUrl = window.location.pathname.endsWith('/') 
            ? window.location.pathname.slice(0, -1) 
            : window.location.pathname
          
          // 使用Vue Router导航替代直接修改location
          window.location.href = `${baseUrl}/result/${result.id}`
          
          // 添加导航成功日志
          console.log(`导航到结果页: ${baseUrl}/result/${result.id}`)
        } else {
          // 设置错误信息并记录详细日志
          console.error('服务器响应格式不正确:', result)
          errorMsg.value = '处理成功但响应格式不正确，请联系管理员'
        }
      } catch (error) {
        console.error('上传照片失败详情:', error)
        
        // 根据错误类型设置不同的错误信息
        if (error.message) {
          errorMsg.value = error.message
        } else {
          errorMsg.value = '上传照片失败，请重试'
        }
        
        // 根据错误状态码显示不同类型的消息
        let messageType = 'error'
        if (error.status === 400) {
          messageType = 'warning'
        } else if (error.status === 404) {
          messageType = 'info'
        }
        
        // 显示消息提示
        ElMessage({
          message: errorMsg.value,
          type: messageType,
          duration: 5000,
          showClose: true
        })
      } finally {
        uploading.value = false
      }
    }
    
    return {
      imageFile,
      imageUrl,
      uploading,
      errorMsg,
      handleFileChange,
      resetImage,
      clearError,
      submitImage
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

/* 添加错误信息样式 */
.error-message {
  width: 100%;
  max-width: 500px;
  margin-top: 1rem;
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
}
</style>