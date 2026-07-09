import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000
})

// 请求拦截器 - 添加token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => {
    const { data } = response
    if (data.code !== 200) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message))
    }
    // 返回 data 字段的内容
    return data.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        ElMessage.error('登录已过期，请重新登录')
        localStorage.removeItem('token')
        window.location.href = '/login'
      } else {
        ElMessage.error(data?.message || '请求失败')
      }
    } else {
      ElMessage.error('网络错误')
    }
    return Promise.reject(error)
  }
)

// 认证相关
export const authApi = {
  login: (username, password) => api.post('/auth/login', { username, password })
}

// 日程相关
export const scheduleApi = {
  getList: (weekOffset = 0) => api.get('/schedules', { params: { week_offset: weekOffset } }),
  create: (data) => api.post('/schedules', data),
  update: (id, data) => api.put(`/schedules/${id}`, data),
  delete: (id) => api.delete(`/schedules/${id}`),
  copyToNextWeek: (sourceOffset = 0, targetOffset = 1) =>
    api.post('/schedules/copy-to-next-week', {
      source_week_offset: sourceOffset,
      target_week_offset: targetOffset
    })
}

// 设置相关
export const settingsApi = {
  get: () => api.get('/settings'),
  update: (data) => api.put('/settings', data),
  getReminderLogs: (limit = 20, offset = 0) =>
    api.get('/settings/reminder-logs', { params: { limit, offset } }),
  testWebhook: (channel, webhook, messagePrefix = '') =>
    api.post('/settings/test-webhook', { channel, webhook, message_prefix: messagePrefix })
}

export default api
