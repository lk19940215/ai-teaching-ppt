/**
 * 全流程监控工具类
 * feat-203: 用于收集接口请求/响应日志，便于与后台比对
 */

/**
 * 监控日志接口
 */
export interface MonitorLog {
  timestamp: number
  type: 'request' | 'response' | 'error' | 'performance'
  endpoint: string
  method: string
  data?: any
  duration?: number
  error?: any
  sessionId?: string
}

/**
 * Monitor 监控类
 * 负责记录和管理所有请求/响应/错误/性能日志
 */
class Monitor {
  private logs: MonitorLog[] = []
  private sessionId: string

  constructor() {
    // 生成唯一会话 ID
    this.sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 获取当前会话 ID
   */
  getSessionId(): string {
    return this.sessionId
  }

  /**
   * 记录请求日志
   * @param endpoint 端点路径
   * @param method HTTP 方法
   * @param data 请求数据
   */
  logRequest(endpoint: string, method: string, data?: any): void {
    const log: MonitorLog = {
      timestamp: Date.now(),
      type: 'request',
      endpoint,
      method: method.toUpperCase(),
      data,
      sessionId: this.sessionId,
    }
    this.logs.push(log)
    console.log('[Monitor Request]', log)
  }

  /**
   * 记录响应日志
   * @param endpoint 端点路径
   * @param method HTTP 方法
   * @param data 响应数据
   * @param duration 耗时（毫秒）
   */
  logResponse(endpoint: string, method: string, data: any, duration: number): void {
    const log: MonitorLog = {
      timestamp: Date.now(),
      type: 'response',
      endpoint,
      method: method.toUpperCase(),
      data,
      duration,
      sessionId: this.sessionId,
    }
    this.logs.push(log)
    console.log('[Monitor Response]', log)
  }

  /**
   * 记录错误日志
   * @param endpoint 端点路径
   * @param method HTTP 方法
   * @param error 错误信息
   */
  logError(endpoint: string, method: string, error: any): void {
    const log: MonitorLog = {
      timestamp: Date.now(),
      type: 'error',
      endpoint,
      method: method.toUpperCase(),
      error: error instanceof Error ? {
        name: error.name,
        message: error.message,
        stack: error.stack,
      } : error,
      sessionId: this.sessionId,
    }
    this.logs.push(log)
    console.error('[Monitor Error]', log)
  }

  /**
   * 记录性能数据
   * @param label 性能标签
   * @param duration 耗时（毫秒）
   */
  logPerformance(label: string, duration: number): void {
    const log: MonitorLog = {
      timestamp: Date.now(),
      type: 'performance',
      endpoint: label,
      method: 'PERFORMANCE',
      duration,
      sessionId: this.sessionId,
    }
    this.logs.push(log)
    console.log('[Monitor Performance]', log)
  }

  /**
   * 获取所有日志
   * @returns 日志数组
   */
  getLogs(): MonitorLog[] {
    return [...this.logs]
  }

  /**
   * 按类型获取日志
   * @param type 日志类型
   * @returns 过滤后的日志数组
   */
  getLogsByType(type: MonitorLog['type']): MonitorLog[] {
    return this.logs.filter(log => log.type === type)
  }

  /**
   * 获取错误日志
   * @returns 错误日志数组
   */
  getErrors(): MonitorLog[] {
    return this.getLogsByType('error')
  }

  /**
   * 导出日志为 JSON 文件下载
   */
  async exportLogs(): Promise<void> {
    const exportData = {
      sessionId: this.sessionId,
      exportTime: new Date().toISOString(),
      totalLogs: this.logs.length,
      summary: {
        requests: this.logs.filter(l => l.type === 'request').length,
        responses: this.logs.filter(l => l.type === 'response').length,
        errors: this.logs.filter(l => l.type === 'error').length,
        performance: this.logs.filter(l => l.type === 'performance').length,
      },
      logs: this.logs,
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `monitor_${this.sessionId}_${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)

    console.log('[Monitor] 日志已导出', {
      sessionId: this.sessionId,
      totalLogs: this.logs.length,
    })
  }

  /**
   * 清空日志并重置会话 ID
   */
  clearLogs(): void {
    this.logs = []
    this.sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    console.log('[Monitor] 日志已清空，新会话 ID:', this.sessionId)
  }

  /**
   * 获取统计信息
   * @returns 统计信息对象
   */
  getStats(): {
    total: number
    byType: Record<string, number>
    avgDuration: number
    errorRate: number
  } {
    const responseLogs = this.logs.filter(l => l.type === 'response' && l.duration)
    const totalDuration = responseLogs.reduce((sum, l) => sum + (l.duration || 0), 0)

    return {
      total: this.logs.length,
      byType: {
        request: this.logs.filter(l => l.type === 'request').length,
        response: this.logs.filter(l => l.type === 'response').length,
        error: this.logs.filter(l => l.type === 'error').length,
        performance: this.logs.filter(l => l.type === 'performance').length,
      },
      avgDuration: responseLogs.length > 0 ? totalDuration / responseLogs.length : 0,
      errorRate: this.logs.length > 0
        ? this.logs.filter(l => l.type === 'error').length / this.logs.length
        : 0,
    }
  }
}

// 导出单例实例
export const monitor = new Monitor()

/**
 * 包装 fetch 函数，自动记录请求/响应/错误
 * @param url 请求 URL
 * @param options fetch 选项
 * @returns Response 对象
 */
export async function monitoredFetch(
  url: string,
  options?: RequestInit
): Promise<Response> {
  // 提取端点路径（移除基础 URL）
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9501'
  const endpoint = url.replace(apiBaseUrl, '').replace(/^\/+/, '/')
  const method = options?.method || 'GET'

  // 记录请求
  let requestData = options?.body
  if (typeof requestData === 'string') {
    try {
      requestData = JSON.parse(requestData)
    } catch {
      // 保持原始字符串
    }
  }
  monitor.logRequest(endpoint, method, requestData)

  const startTime = Date.now()

  try {
    const response = await fetch(url, options)
    const duration = Date.now() - startTime

    // 尝试记录响应数据
    if (response.ok) {
      const clone = response.clone()
      try {
        const data = await clone.json()
        monitor.logResponse(endpoint, method, data, duration)
      } catch {
        // 非 JSON 响应
        monitor.logResponse(endpoint, method, { status: response.status, type: 'non-json' }, duration)
      }
    } else {
      // HTTP 错误响应
      const clone = response.clone()
      let errorData: any = { status: response.status, statusText: response.statusText }
      try {
        errorData = await clone.json()
      } catch {
        // 保持默认错误信息
      }
      monitor.logError(endpoint, method, {
        ...errorData,
        httpStatus: response.status,
      })
    }

    return response
  } catch (error) {
    const duration = Date.now() - startTime
    monitor.logError(endpoint, method, error)
    throw error
  }
}

/**
 * 创建带性能监控的异步函数包装器
 * @param fn 要包装的异步函数
 * @param label 性能标签
 * @returns 包装后的函数
 */
export function withPerformance<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  label: string
): T {
  return (async (...args: Parameters<T>) => {
    const startTime = Date.now()
    try {
      const result = await fn(...args)
      monitor.logPerformance(label, Date.now() - startTime)
      return result
    } catch (error) {
      monitor.logPerformance(`${label}_failed`, Date.now() - startTime)
      throw error
    }
  }) as T
}