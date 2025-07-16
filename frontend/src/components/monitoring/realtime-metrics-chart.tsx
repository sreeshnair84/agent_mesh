'use client'

import React, { useState, useEffect, useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area, BarChart, Bar } from 'recharts'
import { TrendingUp, TrendingDown, Activity, Zap, Clock, Target, Download, Settings, RefreshCw } from 'lucide-react'

interface MetricDataPoint {
  timestamp: string
  value: number
  formatted_timestamp: string
}

interface MetricTrend {
  metric_name: string
  unit: string
  data: MetricDataPoint[]
  aggregation: 'avg' | 'sum' | 'min' | 'max'
  change_percentage: number
  trend_direction: 'up' | 'down' | 'stable'
}

interface RealtimeMetricsChartProps {
  metrics: MetricTrend[]
  timeRange: string
  refreshInterval?: number
  height?: number
  showLegend?: boolean
  chartType?: 'line' | 'area' | 'bar'
}

interface MetricsSummary {
  total_metrics: number
  active_streams: number
  average_value: number
  peak_value: number
  latest_timestamp: string
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function RealtimeMetricsChart({ 
  metrics: initialMetrics = [],
  timeRange = '1h',
  refreshInterval = 5000,
  height = 400,
  showLegend = true,
  chartType = 'line'
}: RealtimeMetricsChartProps) {
  const [metrics, setMetrics] = useState<MetricTrend[]>(initialMetrics)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedMetrics, setSelectedMetrics] = useState<Set<string>>(new Set())
  const [websocket, setWebsocket] = useState<WebSocket | null>(null)
  const [isRealtime, setIsRealtime] = useState(false)
  const [summary, setSummary] = useState<MetricsSummary | null>(null)

  // Color palette for different metrics
  const colors = [
    '#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff7f',
    '#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#6c5ce7'
  ]

  // Fetch metrics data
  const fetchMetrics = async () => {
    setLoading(true)
    setError(null)

    try {
      const endTime = new Date()
      const hours = timeRange === '1h' ? 1 : timeRange === '24h' ? 24 : timeRange === '7d' ? 168 : 720
      const startTime = new Date(endTime.getTime() - (hours * 60 * 60 * 1000))

      const response = await fetch(
        `${API_BASE_URL}/api/v1/monitoring/metrics?` +
        `start_time=${startTime.toISOString()}&` +
        `end_time=${endTime.toISOString()}&` +
        `interval=${timeRange === '1h' ? '1m' : timeRange === '24h' ? '5m' : timeRange === '7d' ? '1h' : '6h'}`
      )

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      // Transform data for chart
      const transformedMetrics: MetricTrend[] = data.metrics.map((metric: any) => ({
        metric_name: metric.metric_name,
        unit: metric.unit,
        data: metric.data_points.map((point: any) => ({
          timestamp: point.timestamp,
          value: point.value,
          formatted_timestamp: new Date(point.timestamp).toLocaleTimeString()
        })),
        aggregation: metric.aggregation,
        change_percentage: metric.change_percentage,
        trend_direction: metric.trend_direction
      }))

      setMetrics(transformedMetrics)
      setSummary({
        total_metrics: transformedMetrics.length,
        active_streams: data.active_streams || 0,
        average_value: data.average_value || 0,
        peak_value: data.peak_value || 0,
        latest_timestamp: data.latest_timestamp || new Date().toISOString()
      })

      // Select first 5 metrics by default
      if (selectedMetrics.size === 0) {
        setSelectedMetrics(new Set(transformedMetrics.slice(0, 5).map(m => m.metric_name)))
      }

    } catch (err) {
      console.error('Error fetching metrics:', err)
      setError('Failed to fetch metrics data')
    } finally {
      setLoading(false)
    }
  }

  // Setup WebSocket for real-time updates
  const setupWebSocket = () => {
    if (websocket) {
      websocket.close()
    }

    const ws = new WebSocket(`ws://localhost:8002/api/v1/monitoring/ws/metrics`)
    
    ws.onopen = () => {
      console.log('Real-time metrics WebSocket connected')
      setIsRealtime(true)
    }
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'metric_update') {
        setMetrics(prev => prev.map(metric => {
          if (metric.metric_name === data.metric_name) {
            const newDataPoint = {
              timestamp: data.timestamp,
              value: data.value,
              formatted_timestamp: new Date(data.timestamp).toLocaleTimeString()
            }
            
            // Add new point and keep only last 100 points
            const updatedData = [...metric.data, newDataPoint].slice(-100)
            
            return {
              ...metric,
              data: updatedData
            }
          }
          return metric
        }))
      }
    }
    
    ws.onclose = () => {
      console.log('Real-time metrics WebSocket disconnected')
      setIsRealtime(false)
      // Reconnect after 5 seconds
      setTimeout(setupWebSocket, 5000)
    }
    
    setWebsocket(ws)
  }

  // Prepare chart data
  const chartData = useMemo(() => {
    if (metrics.length === 0) return []

    // Get all unique timestamps
    const allTimestamps = new Set<string>()
    metrics.forEach(metric => {
      metric.data.forEach(point => allTimestamps.add(point.timestamp))
    })

    // Sort timestamps
    const sortedTimestamps = Array.from(allTimestamps).sort()

    // Create data points for chart
    return sortedTimestamps.map(timestamp => {
      const dataPoint: any = {
        timestamp,
        formatted_timestamp: new Date(timestamp).toLocaleTimeString()
      }

      metrics.forEach(metric => {
        const point = metric.data.find(p => p.timestamp === timestamp)
        dataPoint[metric.metric_name] = point?.value || null
      })

      return dataPoint
    })
  }, [metrics])

  // Format value for display
  const formatValue = (value: number | null, unit: string) => {
    if (value === null) return 'N/A'
    
    switch (unit) {
      case 'percent':
        return `${value.toFixed(1)}%`
      case 'seconds':
        return `${value.toFixed(2)}s`
      case 'milliseconds':
        return `${value.toFixed(0)}ms`
      case 'bytes':
        return value > 1024 * 1024 * 1024 
          ? `${(value / 1024 / 1024 / 1024).toFixed(1)}GB`
          : value > 1024 * 1024 
            ? `${(value / 1024 / 1024).toFixed(1)}MB`
            : `${(value / 1024).toFixed(1)}KB`
      case 'count':
        return value.toLocaleString()
      default:
        return value.toFixed(2)
    }
  }

  // Get trend icon
  const getTrendIcon = (direction: string, changePercentage: number) => {
    if (Math.abs(changePercentage) < 1) {
      return <Activity className="h-4 w-4 text-gray-500" />
    }
    
    return direction === 'up' ? (
      <TrendingUp className="h-4 w-4 text-green-500" />
    ) : (
      <TrendingDown className="h-4 w-4 text-red-500" />
    )
  }

  // Toggle metric selection
  const toggleMetric = (metricName: string) => {
    setSelectedMetrics(prev => {
      const newSelection = new Set(prev)
      if (newSelection.has(metricName)) {
        newSelection.delete(metricName)
      } else {
        newSelection.add(metricName)
      }
      return newSelection
    })
  }

  // Export chart data
  const exportData = () => {
    const csv = [
      ['Timestamp', ...metrics.map(m => m.metric_name)].join(','),
      ...chartData.map(row => [
        row.timestamp,
        ...metrics.map(m => row[m.metric_name] || '')
      ].join(','))
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `metrics-${timeRange}-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Render chart based on type
  const renderChart = () => {
    const selectedMetricsList = metrics.filter(m => selectedMetrics.has(m.metric_name))
    
    if (selectedMetricsList.length === 0) {
      return (
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">Select metrics to display</p>
        </div>
      )
    }

    const commonProps = {
      width: '100%',
      height,
      data: chartData,
      margin: { top: 5, right: 30, left: 20, bottom: 5 }
    }

    switch (chartType) {
      case 'area':
        return (
          <ResponsiveContainer {...commonProps}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="formatted_timestamp" />
              <YAxis />
              <Tooltip 
                formatter={(value: any, name: string) => {
                  const metric = metrics.find(m => m.metric_name === name)
                  return [formatValue(value, metric?.unit || ''), name]
                }}
              />
              {showLegend && <Legend />}
              {selectedMetricsList.map((metric, index) => (
                <Area
                  key={metric.metric_name}
                  type="monotone"
                  dataKey={metric.metric_name}
                  stroke={colors[index % colors.length]}
                  fill={colors[index % colors.length]}
                  fillOpacity={0.6}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        )

      case 'bar':
        return (
          <ResponsiveContainer {...commonProps}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="formatted_timestamp" />
              <YAxis />
              <Tooltip 
                formatter={(value: any, name: string) => {
                  const metric = metrics.find(m => m.metric_name === name)
                  return [formatValue(value, metric?.unit || ''), name]
                }}
              />
              {showLegend && <Legend />}
              {selectedMetricsList.map((metric, index) => (
                <Bar
                  key={metric.metric_name}
                  dataKey={metric.metric_name}
                  fill={colors[index % colors.length]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        )

      default: // line
        return (
          <ResponsiveContainer {...commonProps}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="formatted_timestamp" />
              <YAxis />
              <Tooltip 
                formatter={(value: any, name: string) => {
                  const metric = metrics.find(m => m.metric_name === name)
                  return [formatValue(value, metric?.unit || ''), name]
                }}
              />
              {showLegend && <Legend />}
              {selectedMetricsList.map((metric, index) => (
                <Line
                  key={metric.metric_name}
                  type="monotone"
                  dataKey={metric.metric_name}
                  stroke={colors[index % colors.length]}
                  strokeWidth={2}
                  dot={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )
    }
  }

  useEffect(() => {
    fetchMetrics()
    setupWebSocket()

    const interval = setInterval(fetchMetrics, refreshInterval)

    return () => {
      clearInterval(interval)
      if (websocket) {
        websocket.close()
      }
    }
  }, [timeRange, refreshInterval])

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Real-time Metrics</h3>
          <div className="flex items-center space-x-4 mt-1">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${isRealtime ? 'bg-green-500' : 'bg-gray-400'}`} />
              <span className="text-sm text-gray-600">
                {isRealtime ? 'Live' : 'Disconnected'}
              </span>
            </div>
            {summary && (
              <span className="text-sm text-gray-600">
                {summary.total_metrics} metrics • Last updated: {new Date(summary.latest_timestamp).toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={exportData}
            className="btn-sm btn-secondary"
            disabled={metrics.length === 0}
          >
            <Download className="h-4 w-4 mr-1" />
            Export
          </button>
          <button
            onClick={fetchMetrics}
            className="btn-sm btn-secondary"
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Metrics Summary */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600">Total Metrics</p>
                <p className="text-2xl font-bold text-blue-700">{summary.total_metrics}</p>
              </div>
              <Target className="h-8 w-8 text-blue-600" />
            </div>
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-600">Active Streams</p>
                <p className="text-2xl font-bold text-green-700">{summary.active_streams}</p>
              </div>
              <Activity className="h-8 w-8 text-green-600" />
            </div>
          </div>
          <div className="bg-purple-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-600">Average Value</p>
                <p className="text-2xl font-bold text-purple-700">{summary.average_value.toFixed(2)}</p>
              </div>
              <Activity className="h-8 w-8 text-purple-600" />
            </div>
          </div>
          <div className="bg-orange-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-orange-600">Peak Value</p>
                <p className="text-2xl font-bold text-orange-700">{summary.peak_value.toFixed(2)}</p>
              </div>
              <Zap className="h-8 w-8 text-orange-600" />
            </div>
          </div>
        </div>
      )}

      {/* Metric Selection */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Select Metrics to Display</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {metrics.map((metric) => (
            <div
              key={metric.metric_name}
              className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                selectedMetrics.has(metric.metric_name)
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => toggleMetric(metric.metric_name)}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-900">
                      {metric.metric_name}
                    </span>
                    {getTrendIcon(metric.trend_direction, metric.change_percentage)}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    {metric.change_percentage > 0 ? '+' : ''}{metric.change_percentage.toFixed(1)}% from last period
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={selectedMetrics.has(metric.metric_name)}
                  onChange={() => toggleMetric(metric.metric_name)}
                  className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="mb-4">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-64">
            <p className="text-red-500">{error}</p>
          </div>
        ) : (
          renderChart()
        )}
      </div>
    </div>
  )
}

export default RealtimeMetricsChart
