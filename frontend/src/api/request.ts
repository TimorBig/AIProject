/**
 * API 请求封装模块
 * 统一处理请求拦截、响应拦截、错误处理
 */
import Taro from '@tarojs/taro'

// 请求配置接口
interface RequestConfig {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: Record<string, unknown>
  header?: Record<string, string>
  showLoading?: boolean
  loadingText?: string
}

// 响应数据接口
interface ResponseData<T = unknown> {
  code: number
  message: string
  data: T
}

// API 基础地址
const BASE_URL = process.env.API_BASE_URL || 'http://localhost:5000/api/v1'

/**
 * 统一请求方法
 * @param config 请求配置
 * @returns Promise<T>
 */
export async function request<T>(config: RequestConfig): Promise<T> {
  const {
    url,
    method = 'GET',
    data = {},
    header = {},
    showLoading = false,
    loadingText = '加载中...'
  } = config

  // 显示加载提示
  if (showLoading) {
    Taro.showLoading({ title: loadingText, mask: true })
  }

  try {
    // 获取 token
    const token = Taro.getStorageSync('token')
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...header
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await Taro.request({
      url: `${BASE_URL}${url}`,
      method,
      data,
      header: headers
    })

    if (showLoading) {
      Taro.hideLoading()
    }

    const result = response.data as ResponseData<T>

    // 请求成功
    if (result.code === 0) {
      return result.data
    }

    // 业务错误
    Taro.showToast({
      title: result.message || '请求失败',
      icon: 'none'
    })
    return Promise.reject(new Error(result.message))

  } catch (error) {
    if (showLoading) {
      Taro.hideLoading()
    }
    
    Taro.showToast({
      title: '网络错误，请稍后重试',
      icon: 'none'
    })
    return Promise.reject(error)
  }
}

export default request
