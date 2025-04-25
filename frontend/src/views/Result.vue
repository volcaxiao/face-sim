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
    
    <div v-else class="result-content" ref="resultContent">
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
              <el-card shadow="hover" class="celebrity-card-inner" @click="viewCelebrityDetail(detail.celebrity)">
                <div class="celebrity-info">
                  <img :src="detail.celebrity.photo_url" class="celebrity-photo" :alt="detail.celebrity.name" />
                  <div class="celebrity-data">
                    <h4>{{ detail.celebrity.name }}</h4>
                    <div class="similarity">
                      <div class="similarity-value">{{ formatSimilarity(detail.similarity) }}%</div>
                      <el-progress 
                        :percentage="detail.similarity" 
                        :color="getSimilarityColor(detail.similarity)" 
                        :stroke-width="10" 
                        :show-text="false" />
                    </div>
                    <div class="celebrity-basic-info">
                      <div class="info-item" v-if="detail.celebrity.nationality">
                        <span class="info-label">国籍:</span> {{ detail.celebrity.nationality }}
                      </div>
                      <div class="info-item" v-if="detail.celebrity.occupation">
                        <span class="info-label">职业:</span> {{ detail.celebrity.occupation }}
                      </div>
                      <div class="info-item" v-if="detail.celebrity.birth_date">
                        <span class="info-label">出生日期:</span> {{ formatDate(detail.celebrity.birth_date) }}
                      </div>
                    </div>
                    <div class="celebrity-action">
                      <el-button type="primary" size="small" plain @click.stop="openCelebrityUrl(detail.celebrity.detail_url, detail.celebrity.name)" v-if="detail.celebrity.detail_url">
                        查看详细资料
                      </el-button>
                    </div>
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 明星详情对话框 -->
      <el-dialog
        v-model="celebDetailVisible"
        :title="selectedCelebrity?.name || '明星详情'"
        width="600px"
        v-if="selectedCelebrity"
      >
        <div class="celebrity-detail-container">
          <div class="celebrity-detail-photo">
            <img :src="selectedCelebrity.photo_url" :alt="selectedCelebrity.name" />
          </div>
          <div class="celebrity-detail-info">
            <h3>{{ selectedCelebrity.name }}</h3>
            
            <div class="detail-info-section">
              <div class="detail-info-item" v-if="selectedCelebrity.nationality">
                <span class="detail-label">国籍：</span>
                <span>{{ selectedCelebrity.nationality }}</span>
              </div>
              <div class="detail-info-item" v-if="selectedCelebrity.occupation">
                <span class="detail-label">职业：</span>
                <span>{{ selectedCelebrity.occupation }}</span>
              </div>
              <div class="detail-info-item" v-if="selectedCelebrity.birth_date">
                <span class="detail-label">出生日期：</span>
                <span>{{ formatDate(selectedCelebrity.birth_date) }}</span>
              </div>
            </div>
            
            <div class="detail-description" v-if="selectedCelebrity.description">
              <h4>简介</h4>
              <p>{{ selectedCelebrity.description }}</p>
            </div>
            
            <div class="detail-works" v-if="selectedCelebrity.works">
              <h4>代表作品</h4>
              <p>{{ selectedCelebrity.works }}</p>
            </div>
            
            <div class="detail-actions">
              <el-button type="primary" @click="openCelebrityUrl(selectedCelebrity.detail_url, selectedCelebrity.name)" v-if="selectedCelebrity.detail_url">
                查看更多资料
              </el-button>
            </div>
          </div>
        </div>
      </el-dialog>
      
      <div class="actions">
        <el-button type="primary" @click="$router.push('/')">再来一次</el-button>
        <el-button type="success" @click="showShareOptions">分享结果</el-button>
      </div>
      
      <!-- 分享选项对话框 -->
      <el-dialog
        v-model="shareDialogVisible"
        title="分享您的明星脸匹配结果"
        width="450px"
      >
        <div v-if="isSharing" class="share-loading">
          <el-spin></el-spin>
          <p>正在生成分享链接...</p>
        </div>
        <div v-else-if="shareError" class="share-error">
          <el-alert
            :title="shareError"
            type="error"
            :closable="false"
            show-icon
          ></el-alert>
          <div class="share-error-actions">
            <el-button @click="shareDialogVisible = false">关闭</el-button>
            <el-button type="primary" @click="generateShareLink">重试</el-button>
          </div>
        </div>
        <div v-else-if="shareData" class="share-success">
          <div class="share-info">
            <p class="share-tip">您的测试结果已设为公开分享。复制以下链接分享给好友：</p>
            <div class="share-link-container">
              <el-input
                v-model="shareData.share_url"
                readonly
                class="share-link-input"
              >
                <template #append>
                  <el-button @click="copyShareLink(shareData.share_url)">复制</el-button>
                </template>
              </el-input>
            </div>
            <div class="share-qrcode" v-if="shareQRCode">
              <p>扫描二维码分享结果</p>
              <img :src="shareQRCode" alt="分享二维码" class="qrcode-img">
            </div>
          </div>
          <div class="share-actions">
            <el-button @click="shareDialogVisible = false">关闭</el-button>
            <el-button type="primary" @click="copyShareLink(shareData.share_url)">复制链接</el-button>
          </div>
        </div>
        <div v-else class="share-confirm">
          <p>分享此测试结果将会将其设为公开访问，任何获得链接的人都可以查看。</p>
          <p>确定要继续吗？</p>
          <div class="share-confirm-actions">
            <el-button @click="shareDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="generateShareLink">确认分享</el-button>
          </div>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getComparisonResult, shareComparisonResult } from '../services/api'
import { ElMessage } from 'element-plus'
import html2canvas from 'html2canvas'

export default {
  name: 'Result',
  setup() {
    const route = useRoute()
    const loading = ref(true)
    const error = ref('')
    const result = ref(null)
    const shareDialogVisible = ref(false)
    const resultContent = ref(null)
    const celebDetailVisible = ref(false)
    const selectedCelebrity = ref(null)
    const isSharing = ref(false)
    const shareError = ref('')
    const shareData = ref(null)
    const shareQRCode = ref(null)
    
    const fetchResultData = async () => {
      const id = route.params.id
      if (!id) {
        error.value = '无效的结果ID'
        loading.value = false
        return
      }
      
      try {
        console.log('正在获取结果数据，ID:', id)
        
        // 检查是否为公开分享的链接
        const isPublic = route.query.public === 'true'
        console.log('是否为公开分享链接:', isPublic)
        
        // 调用API获取结果，传递公开标志
        const params = isPublic ? { public: 'true' } : {}
        const data = await getComparisonResult(id, params)
        console.log('API返回的结果数据:', data)
        
        if (!data || !data.details || data.details.length === 0) {
          error.value = '未找到比对结果，可能已过期或被删除'
          loading.value = false
          return
        }
        
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
    
    const formatDate = (dateStr) => {
      if (!dateStr) return '';
      
      try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) {
          // 如果日期无效，直接返回原始字符串
          return dateStr;
        }
        return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`;
      } catch (e) {
        return dateStr;
      }
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
    
    const viewCelebrityDetail = (celebrity) => {
      selectedCelebrity.value = celebrity;
      celebDetailVisible.value = true;
    }
    
    const openCelebrityUrl = (url, name) => {
      if (!url) {
        ElMessage({
          message: '该明星暂无更多详细资料',
          type: 'warning'
        });
        return;
      }
      
      if (url && !url.startsWith('http')) {
        url = 'https://' + url;
      }
      
      console.log(`用户点击了明星 ${name} 的链接: ${url}`);
      window.open(url, '_blank');
    }

    const showShareOptions = () => {
      shareDialogVisible.value = true
    }
    
    const generateShareLink = async () => {
      if (!result.value || !result.value.id) {
        shareError.value = '无法获取结果ID，无法生成分享链接'
        return
      }
      
      isSharing.value = true
      shareError.value = ''
      shareData.value = null
      
      try {
        // 调用API设置比对结果为公开分享
        const response = await shareComparisonResult(result.value.id)
        shareData.value = response
        
        // 生成二维码，使用第三方服务
        if (response.share_url) {
          const encodedUrl = encodeURIComponent(response.share_url)
          shareQRCode.value = `https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodedUrl}`
        }
      } catch (err) {
        console.error('生成分享链接失败:', err)
        shareError.value = err.message || '生成分享链接失败，请稍后重试'
      } finally {
        isSharing.value = false
      }
    }
    
    const copyShareLink = (link) => {
      navigator.clipboard.writeText(link).then(() => {
        ElMessage({
          message: '链接已复制到剪贴板',
          type: 'success'
        })
      }).catch(() => {
        ElMessage.error('复制失败，请手动复制')
      })
    }

    onMounted(() => {
      fetchResultData()
    })
    
    return {
      loading,
      error,
      result,
      resultContent,
      formatSimilarity,
      formatDate,
      getSimilarityColor,
      truncateText,
      openCelebrityUrl,
      shareDialogVisible,
      showShareOptions,
      generateShareLink,
      copyShareLink,
      celebDetailVisible,
      selectedCelebrity,
      viewCelebrityDetail,
      isSharing,
      shareError,
      shareData,
      shareQRCode
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
  font-weight: bold;
}

.celebrities-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.celebrity-card {
  margin-bottom: 1rem;
}

.celebrity-card-inner {
  transition: all 0.3s ease;
  height: 100%;
  cursor: pointer;
}

.celebrity-card-inner:hover {
  transform: translateY(-5px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.15);
}

.celebrity-info {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.celebrity-photo {
  width: 100%;
  height: 180px;
  object-fit: cover;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.celebrity-data {
  width: 100%;
  text-align: center;
}

.celebrity-data h4 {
  margin: 0.5rem 0;
  color: #303133;
  font-size: 1.2rem;
}

.similarity {
  margin: 0.5rem 0;
}

.similarity-value {
  text-align: center;
  margin-bottom: 0.25rem;
  font-weight: bold;
  font-size: 1.5rem;
  color: #409eff;
}

.celebrity-basic-info {
  margin: 0.75rem 0;
  text-align: left;
  padding: 0 0.5rem;
}

.info-item {
  margin: 0.35rem 0;
  font-size: 0.9rem;
  color: #606266;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.info-label {
  color: #909399;
  margin-right: 0.25rem;
}

.celebrity-action {
  margin-top: 0.75rem;
}

.actions {
  text-align: center;
  margin-top: 1.5rem;
}

.share-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  padding: 0.5rem;
}

.share-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  padding: 1rem;
  border-radius: 8px;
  transition: background-color 0.3s ease;
}

.share-option:hover {
  background-color: #f5f7fa;
}

.share-option .el-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.share-option-text {
  font-size: 0.9rem;
  color: #606266;
}

/* 明星详情对话框样式 */
.celebrity-detail-container {
  display: flex;
  gap: 1.5rem;
}

.celebrity-detail-photo {
  flex: 0 0 40%;
}

.celebrity-detail-photo img {
  width: 100%;
  border-radius: 8px;
  object-fit: cover;
}

.celebrity-detail-info {
  flex: 1;
}

.celebrity-detail-info h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: #303133;
  font-size: 1.5rem;
}

.detail-info-section {
  margin-bottom: 1.5rem;
}

.detail-info-item {
  margin: 0.5rem 0;
  display: flex;
}

.detail-label {
  color: #909399;
  width: 80px;
  flex-shrink: 0;
}

.detail-description h4,
.detail-works h4 {
  margin: 1rem 0 0.5rem;
  font-size: 1.1rem;
  color: #606266;
}

.detail-description p,
.detail-works p {
  margin: 0.5rem 0;
  color: #606266;
  line-height: 1.5;
}

.detail-actions {
  margin-top: 1.5rem;
}

.share-loading {
  text-align: center;
  padding: 1rem;
}

.share-error {
  text-align: center;
  padding: 1rem;
}

.share-error-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-top: 1rem;
}

.share-success {
  text-align: center;
  padding: 1rem;
}

.share-info {
  margin-bottom: 1rem;
}

.share-tip {
  margin-bottom: 0.5rem;
  color: #606266;
}

.share-link-container {
  margin-bottom: 1rem;
}

.share-link-input {
  width: 100%;
}

.qrcode-img {
  width: 150px;
  height: 150px;
  margin-top: 0.5rem;
}

.share-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.share-confirm {
  text-align: center;
  padding: 1rem;
}

.share-confirm-actions {
  display: flex;
  justify-content: center;
  gap: 1rem;
  margin-top: 1rem;
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
  
  .celebrity-detail-container {
    flex-direction: column;
  }
  
  .celebrity-detail-photo {
    margin-bottom: 1rem;
    flex: none;
  }
}
</style>