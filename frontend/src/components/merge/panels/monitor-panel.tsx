'use client'

/**
 * 监控面板组件
 * feat-204: 实时显示 API 请求/响应日志，支持导出和清空
 */

import { useState, useEffect, useCallback } from 'react'
import { monitor, MonitorLog } from '@/utils/monitor'

/**
 * 获取日志类型对应的样式类名
 * @param type 日志类型
 * @returns Tailwind 类名字符串
 */
function getLogStyle(type: MonitorLog['type']): string {
  switch (type) {
    case 'error':
      return 'bg-red-50 text-red-700 border-l-2 border-red-400'
    case 'performance':
      return 'bg-yellow-50 text-yellow-800 border-l-2 border-yellow-400'
    case 'response':
      return 'bg-green-50 text-green-700 border-l-2 border-green-400'
    case 'request':
    default:
      return 'bg-gray-50 text-gray-700 border-l-2 border-gray-300'
  }
}

/**
 * 获取日志类型对应的 emoji
 * @param type 日志类型
 * @returns emoji 字符串
 */
function getTypeEmoji(type: MonitorLog['type']): string {
  switch (type) {
    case 'request':
      return '📤'
    case 'response':
      return '📥'
    case 'error':
      return '❌'
    case 'performance':
      return '⏱️'
    default:
      return '📝'
  }
}

export function MonitorPanel() {
  const [logs, setLogs] = useState<MonitorLog[]>([])
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [isMinimized, setIsMinimized] = useState(false)

  // 刷新日志
  const refreshLogs = useCallback(() => {
    setLogs(monitor.getLogs())
  }, [])

  // 自动刷新定时器
  useEffect(() => {
    if (autoRefresh) {
      refreshLogs() // 立即刷新一次
      const interval = setInterval(refreshLogs, 1000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh, refreshLogs])

  // 导出日志
  const handleExport = () => {
    monitor.exportLogs()
  }

  // 清空日志
  const handleClear = () => {
    monitor.clearLogs()
    setLogs([])
  }

  // 获取统计信息
  const stats = monitor.getStats()

  return (
    <div
      className={`fixed bottom-4 right-4 bg-white border border-gray-200 rounded-lg shadow-xl z-50 transition-all duration-300 ${
        isMinimized ? 'w-auto' : 'w-96'
      }`}
    >
      {/* 标题栏 */}
      <div className="border-b border-gray-200 p-2 flex justify-between items-center bg-gray-50 rounded-t-lg">
        <div className="flex items-center gap-2">
          <span className="text-lg">📊</span>
          <h3 className="text-sm font-semibold text-gray-700">监控面板</h3>
          {!isMinimized && (
            <span className="text-xs text-gray-500">
              ({stats.total} 条)
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {/* 最小化按钮 */}
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="text-xs px-2 py-1 text-gray-600 hover:bg-gray-200 rounded transition-colors"
            title={isMinimized ? '展开' : '最小化'}
          >
            {isMinimized ? '📖' : '📕'}
          </button>
        </div>
      </div>

      {/* 展开内容 */}
      {!isMinimized && (
        <>
          {/* 工具栏 */}
          <div className="border-b border-gray-100 p-2 flex justify-between items-center bg-gray-50/50">
            <div className="flex gap-1">
              <button
                onClick={handleExport}
                disabled={logs.length === 0}
                className="text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                title="导出日志为 JSON 文件"
              >
                📥 导出
              </button>
              <button
                onClick={handleClear}
                disabled={logs.length === 0}
                className="text-xs px-2 py-1 bg-red-500 text-white rounded hover:bg-red-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                title="清空所有日志"
              >
                🗑️ 清空
              </button>
            </div>
            <label className="flex items-center gap-1 text-xs text-gray-600 cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="w-3 h-3 rounded border-gray-300 text-blue-500 focus:ring-blue-500"
              />
              <span>自动刷新</span>
            </label>
          </div>

          {/* 统计信息 */}
          {logs.length > 0 && (
            <div className="border-b border-gray-100 px-2 py-1 flex gap-2 text-xs bg-gray-50/30">
              <span className="text-gray-600">
                📤 {stats.byType.request}
              </span>
              <span className="text-green-600">
                📥 {stats.byType.response}
              </span>
              {stats.byType.error > 0 && (
                <span className="text-red-600">
                  ❌ {stats.byType.error}
                </span>
              )}
              {stats.byType.performance > 0 && (
                <span className="text-yellow-600">
                  ⏱️ {stats.byType.performance}
                </span>
              )}
              {stats.avgDuration > 0 && (
                <span className="text-gray-500">
                  平均 {Math.round(stats.avgDuration)}ms
                </span>
              )}
            </div>
          )}

          {/* 日志列表 */}
          <div className="p-2 max-h-80 overflow-y-auto text-xs font-mono">
            {logs.length === 0 ? (
              <div className="text-center text-gray-400 py-8">
                <p className="text-2xl mb-2">📭</p>
                <p>暂无日志</p>
                <p className="text-xs mt-1">执行操作后将自动记录</p>
              </div>
            ) : (
              <div className="space-y-1">
                {logs.map((log, index) => (
                  <div
                    key={`${log.timestamp}-${index}`}
                    className={`py-1.5 px-2 rounded text-xs ${getLogStyle(log.type)}`}
                    title={JSON.stringify(log, null, 2)}
                  >
                    <div className="flex items-start gap-1">
                      <span className="shrink-0">{getTypeEmoji(log.type)}</span>
                      <div className="flex-1 min-w-0">
                        <div className="truncate font-medium">
                          {log.method} {log.endpoint}
                        </div>
                        <div className="text-gray-500 truncate">
                          {log.duration ? `${log.duration}ms` : ''}
                          {log.error?.message && ` - ${log.error.message}`}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 底部信息 */}
          <div className="border-t border-gray-100 px-2 py-1 text-xs text-gray-400 bg-gray-50/30 rounded-b-lg">
            <span>Session: {monitor.getSessionId().slice(0, 20)}...</span>
          </div>
        </>
      )}
    </div>
  )
}