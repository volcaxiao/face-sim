import axios from 'axios'

// 创建axios实例
const apiClient = axios.create({
  baseURL: process.env.VUE_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  timeout: 60000  // 增加超时时间到60秒，适应照片上传和Face++处理需求
})

// 生成并存储会话ID
const getSessionId = () => {
  let sessionId = localStorage.getItem('face_session_id');
  if (!sessionId) {
    sessionId = 'session_' + Math.random().toString(36).substring(2, 15);
    localStorage.setItem('face_session_id', sessionId);
  }
  return sessionId;
};

// 上传照片并获取相似度比对
export const uploadPhoto = async (photo) => {
  const formData = new FormData()
  formData.append('photo', photo)
  
  // 添加会话ID到请求中
  const sessionId = getSessionId();
  formData.append('session_id', sessionId);
  
  try {
    console.log('开始上传照片，大小: ' + (photo.size / 1024).toFixed(2) + ' KB')
    const response = await apiClient.post('/api/compare/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      // 添加上传进度事件处理
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        console.log(`上传进度: ${percentCompleted}%`)
      }
    })
    console.log('上传成功，服务器响应:', response.data)
    return response.data
  } catch (error) {
    console.error('上传照片失败:', error)
    // 提供更详细的错误日志，帮助调试
    if (error.response) {
      // 服务器返回了错误状态码
      console.error('服务器响应错误状态码:', error.response.status)
      console.error('服务器响应数据:', error.response.data)
    } else if (error.request) {
      // 请求已发送但没有收到响应
      console.error('没有收到服务器响应，请求详情:', error.request)
      console.error('请求超时或网络问题')
    } else {
      // 请求设置过程中出现问题
      console.error('请求配置错误:', error.message)
    }
    
    // 提取后端返回的错误信息
    let errorMessage = '上传照片失败，请重试';
    if (error.response && error.response.data) {
      if (error.response.data.error) {
        errorMessage = error.response.data.error;
      } else if (error.response.data.detail) {
        errorMessage = error.response.data.detail;
      }
    } else if (error.code === 'ECONNABORTED') {
      errorMessage = '上传超时，请确保网络稳定并重试';
    }
    
    // 将错误信息包装后抛出，便于上层组件处理
    throw {
      message: errorMessage,
      originalError: error,
      status: error.response ? error.response.status : null
    };
  }
}

// 获取比对结果详情
export const getComparisonResult = async (id, additionalParams = {}) => {
  // 添加会话ID到查询参数
  const sessionId = getSessionId();
  const params = { session_id: sessionId, ...additionalParams };
  
  try {
    const response = await apiClient.get(`/api/compare/${id}/`, { params })
    return response.data
  } catch (error) {
    console.error('获取比对结果失败:', error)
    // 提取后端返回的错误信息
    let errorMessage = '获取比对结果失败';
    if (error.response && error.response.data) {
      if (error.response.data.error) {
        errorMessage = error.response.data.error;
      } else if (error.response.data.detail) {
        errorMessage = error.response.data.detail;
      }
    }
    throw {
      message: errorMessage,
      originalError: error,
      status: error.response ? error.response.status : null
    };
  }
}

// 获取处理状态和进度
export const getComparisonStatus = async (id) => {
  // 添加会话ID到查询参数
  const sessionId = getSessionId();
  const params = { session_id: sessionId };
  
  try {
    const response = await apiClient.get(`/api/compare/status/${id}/`, { params })
    console.log('获取状态成功:', response.data)
    return response.data
  } catch (error) {
    console.error('获取处理状态失败:', error)
    let errorMessage = '获取处理状态失败';
    if (error.response && error.response.data) {
      if (error.response.data.error) {
        errorMessage = error.response.data.error;
      } else if (error.response.data.detail) {
        errorMessage = error.response.data.detail;
      } else if (typeof error.response.data === 'string') {
        // 处理可能的纯字符串错误信息
        errorMessage = error.response.data;
      }
    } else if (error.code === 'ECONNABORTED') {
      errorMessage = '请求超时，请检查网络连接';
    } else if (!error.response) {
      errorMessage = '无法连接到服务器，请检查网络连接';
    }
    
    throw {
      message: errorMessage,
      originalError: error,
      status: error.response ? error.response.status : null
    };
  }
}

// 获取所有名人列表
export const getCelebrities = async () => {
  try {
    const response = await apiClient.get('/api/celebrities/')
    return response.data
  } catch (error) {
    console.error('获取名人列表失败:', error)
    // 提取后端返回的错误信息
    let errorMessage = '获取名人列表失败';
    if (error.response && error.response.data) {
      if (error.response.data.error) {
        errorMessage = error.response.data.error;
      } else if (error.response.data.detail) {
        errorMessage = error.response.data.detail;
      }
    }
    throw {
      message: errorMessage,
      originalError: error,
      status: error.response ? error.response.status : null
    };
  }
}

// 新增：获取历史比对记录
export const getComparisonHistory = async () => {
  // 仅获取当前会话的历史记录
  const sessionId = getSessionId();
  
  try {
    const response = await apiClient.get(`/api/compare/history/`, { 
      params: { session_id: sessionId }
    })
    return response.data
  } catch (error) {
    console.error('获取历史记录失败:', error)
    let errorMessage = '获取历史记录失败';
    if (error.response && error.response.data && error.response.data.error) {
      errorMessage = error.response.data.error;
    }
    throw { message: errorMessage };
  }
}

// 设置比对结果为公开分享
export const shareComparisonResult = async (id) => {
  // 添加会话ID到请求参数
  const sessionId = getSessionId();
  
  try {
    const response = await apiClient.post(`/api/compare/share/${id}/`, { 
      session_id: sessionId 
    })
    console.log('设置分享成功:', response.data)
    return response.data
  } catch (error) {
    console.error('设置分享失败:', error)
    let errorMessage = '设置分享失败';
    if (error.response && error.response.data) {
      if (error.response.data.error) {
        errorMessage = error.response.data.error;
      } else if (error.response.data.detail) {
        errorMessage = error.response.data.detail;
      }
    }
    throw {
      message: errorMessage,
      originalError: error,
      status: error.response ? error.response.status : null
    };
  }
}