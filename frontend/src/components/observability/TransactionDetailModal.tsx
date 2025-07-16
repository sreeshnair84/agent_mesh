import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { X, Clock, User, Zap, Database, AlertCircle, CheckCircle, Activity, Copy } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import { apiClient } from '@/lib/api-client'

interface AgentInteraction {
  id: string
  agent_name: string
  timestamp: string
  duration: number
  status: 'success' | 'error' | 'pending'
  input: any
  output: any
  error?: string
  llm_tokens: number
  model_name: string
}

interface Transaction {
  id: string
  session_id: string
  trace_id: string
  timestamp: string
  status: 'success' | 'error' | 'pending'
  duration: number
  agent_name: string
  workflow_name?: string
  error_message?: string
  request_count: number
  llm_tokens: number
  interactions?: AgentInteraction[]
  metadata?: Record<string, any>
}

interface TransactionDetailModalProps {
  transaction: Transaction
  onClose: () => void
}

export function TransactionDetailModal({ transaction, onClose }: TransactionDetailModalProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'timeline' | 'interactions' | 'llm' | 'metadata'>('overview')
  const [expandedInteraction, setExpandedInteraction] = useState<string | null>(null)

  // Fetch detailed transaction data
  const { data: transactionDetails, isLoading } = useQuery({
    queryKey: ['transaction-details', transaction.id],
    queryFn: () => apiClient.get(`/observability/transactions/${transaction.id}`),
    enabled: !!transaction.id
  })

  const detailedTransaction = (transactionDetails?.data || transaction) as Transaction
  const interactions = detailedTransaction.interactions || []

  const statusColors = {
    success: 'bg-green-100 text-green-800',
    error: 'bg-red-100 text-red-800',
    pending: 'bg-yellow-100 text-yellow-800'
  }

  const StatusIcon = ({ status }: { status: string }) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />
      case 'pending':
        return <Activity className="w-4 h-4 text-yellow-600 animate-pulse" />
      default:
        return <Activity className="w-4 h-4 text-gray-600" />
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const formatPayload = (payload: any) => {
    return JSON.stringify(payload, null, 2)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-3">
            <StatusIcon status={transaction.status} />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Transaction Details</h2>
              <p className="text-sm text-gray-600 font-mono">{transaction.id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <nav className="flex space-x-6 px-6">
            {[
              { key: 'overview', label: 'Overview' },
              { key: 'timeline', label: 'Timeline' },
              { key: 'interactions', label: 'Interactions' },
              { key: 'llm', label: 'LLM Usage' },
              { key: 'metadata', label: 'Metadata' }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.key
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Transaction Info</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Status:</span>
                        <Badge className={statusColors[transaction.status]}>
                          {transaction.status}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Duration:</span>
                        <span className="text-sm font-medium">{transaction.duration}ms</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Timestamp:</span>
                        <span className="text-sm font-medium">{new Date(transaction.timestamp).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Requests:</span>
                        <span className="text-sm font-medium">{transaction.request_count}</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Identifiers</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Session ID:</span>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-mono">{transaction.session_id}</span>
                          <button
                            onClick={() => copyToClipboard(transaction.session_id)}
                            className="p-1 hover:bg-gray-100 rounded"
                          >
                            <Copy className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Trace ID:</span>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-mono">{transaction.trace_id}</span>
                          <button
                            onClick={() => copyToClipboard(transaction.trace_id)}
                            className="p-1 hover:bg-gray-100 rounded"
                          >
                            <Copy className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Agent & Workflow</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Agent:</span>
                        <span className="text-sm font-medium">{transaction.agent_name}</span>
                      </div>
                      {transaction.workflow_name && (
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Workflow:</span>
                          <span className="text-sm font-medium">{transaction.workflow_name}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Performance</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">LLM Tokens:</span>
                        <span className="text-sm font-medium">{transaction.llm_tokens.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Avg Response Time:</span>
                        <span className="text-sm font-medium">{Math.round(transaction.duration / transaction.request_count)}ms</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {transaction.error_message && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <AlertCircle className="w-5 h-5 text-red-600" />
                    <h3 className="font-medium text-red-800">Error Details</h3>
                  </div>
                  <p className="text-sm text-red-700">{transaction.error_message}</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'timeline' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Execution Timeline</h3>
              <div className="relative">
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-300"></div>
                <div className="space-y-4">
                  {interactions.map((interaction, index) => (
                    <div key={interaction.id} className="flex items-start space-x-4">
                      <div className="flex-shrink-0 w-8 h-8 bg-white border-2 border-gray-300 rounded-full flex items-center justify-center">
                        <span className="text-xs font-medium text-gray-600">{index + 1}</span>
                      </div>
                      <div className="flex-1 bg-gray-50 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-gray-900">{interaction.agent_name}</h4>
                          <div className="flex items-center space-x-2">
                            <Badge className={statusColors[interaction.status]}>
                              {interaction.status}
                            </Badge>
                            <span className="text-sm text-gray-600">{interaction.duration}ms</span>
                          </div>
                        </div>
                        <p className="text-sm text-gray-600 mb-1">
                          {new Date(interaction.timestamp).toLocaleString()}
                        </p>
                        {interaction.llm_tokens > 0 && (
                          <p className="text-sm text-gray-600">
                            LLM: {interaction.llm_tokens} tokens ({interaction.model_name})
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'interactions' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Agent Interactions</h3>
              <div className="space-y-4">
                {interactions.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Activity className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                    <p>No interactions found for this transaction</p>
                  </div>
                ) : (
                  interactions.map((interaction) => (
                  <div key={interaction.id} className="border rounded-lg overflow-hidden">
                    <div
                      className="bg-gray-50 p-4 cursor-pointer hover:bg-gray-100 transition-colors"
                      onClick={() => setExpandedInteraction(
                        expandedInteraction === interaction.id ? null : interaction.id
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <StatusIcon status={interaction.status} />
                          <div>
                            <h4 className="font-medium text-gray-900">{interaction.agent_name}</h4>
                            <p className="text-sm text-gray-600">{new Date(interaction.timestamp).toLocaleString()}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-3">
                          <span className="text-sm text-gray-600">{interaction.duration}ms</span>
                          {interaction.llm_tokens > 0 && (
                            <span className="text-sm text-gray-600">{interaction.llm_tokens} tokens</span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {expandedInteraction === interaction.id && (
                      <div className="p-4 border-t">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <h5 className="font-medium text-gray-900 mb-2">Input</h5>
                            <pre className="text-sm bg-gray-100 rounded p-3 overflow-x-auto">
                              {formatPayload(interaction.input)}
                            </pre>
                          </div>
                          <div>
                            <h5 className="font-medium text-gray-900 mb-2">Output</h5>
                            <pre className="text-sm bg-gray-100 rounded p-3 overflow-x-auto">
                              {formatPayload(interaction.output)}
                            </pre>
                          </div>
                        </div>
                        {interaction.error && (
                          <div className="mt-4">
                            <h5 className="font-medium text-red-800 mb-2">Error</h5>
                            <div className="text-sm bg-red-50 border border-red-200 rounded p-3">
                              {interaction.error}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))
                )}
              </div>
            </div>
          )}

          {activeTab === 'llm' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <Zap className="w-5 h-5 text-purple-600" />
                    <h3 className="font-medium text-gray-900">Total Tokens</h3>
                  </div>
                  <p className="text-2xl font-bold text-gray-900">{transaction.llm_tokens.toLocaleString()}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <Database className="w-5 h-5 text-blue-600" />
                    <h3 className="font-medium text-gray-900">Model Calls</h3>
                  </div>
                  <p className="text-2xl font-bold text-gray-900">{interactions.filter(i => i.llm_tokens > 0).length}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <Clock className="w-5 h-5 text-green-600" />
                    <h3 className="font-medium text-gray-900">Avg Tokens/Call</h3>
                  </div>
                  <p className="text-2xl font-bold text-gray-900">
                    {Math.round(transaction.llm_tokens / interactions.filter(i => i.llm_tokens > 0).length)}
                  </p>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Model Usage Breakdown</h3>
                <div className="space-y-3">
                  {interactions.filter(i => i.llm_tokens > 0).map((interaction) => (
                    <div key={interaction.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-900">{interaction.agent_name}</p>
                        <p className="text-sm text-gray-600">{interaction.model_name}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-gray-900">{interaction.llm_tokens.toLocaleString()}</p>
                        <p className="text-sm text-gray-600">tokens</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'metadata' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Transaction Metadata</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                <pre className="text-sm overflow-x-auto">
                  {formatPayload({
                    transaction_id: transaction.id,
                    session_id: transaction.session_id,
                    trace_id: transaction.trace_id,
                    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    client_ip: '192.168.1.100',
                    request_headers: {
                      'content-type': 'application/json',
                      'authorization': 'Bearer ***',
                      'x-request-id': 'req_123456'
                    },
                    environment: 'production',
                    version: '1.0.0'
                  })}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
