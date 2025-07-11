import axios, { AxiosInstance, AxiosRequestConfig } from 'axios'
import { APIResponse, PaginatedResponse } from '@/types'

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized access
          localStorage.removeItem('auth_token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<APIResponse<T>> {
    const response = await this.client.get(url, config)
    return response.data
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<APIResponse<T>> {
    const response = await this.client.post(url, data, config)
    return response.data
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<APIResponse<T>> {
    const response = await this.client.put(url, data, config)
    return response.data
  }

  async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<APIResponse<T>> {
    const response = await this.client.patch(url, data, config)
    return response.data
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<APIResponse<T>> {
    const response = await this.client.delete(url, config)
    return response.data
  }

  async getPaginated<T>(
    url: string, 
    params?: Record<string, any>
  ): Promise<PaginatedResponse<T>> {
    const response = await this.client.get(url, { params })
    return response.data
  }
}

export const apiClient = new APIClient()

// API endpoints
export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    REGISTER: '/api/v1/auth/register',
    REFRESH: '/api/v1/auth/refresh',
    LOGOUT: '/api/v1/auth/logout',
    RESET_PASSWORD: '/api/v1/auth/reset-password',
  },

  // Agents
  AGENTS: {
    BASE: '/api/v1/agents',
    SEARCH: '/api/v1/agents/search',
    SEMANTIC_SEARCH: '/api/v1/agents/search/semantic',
    DEPLOY: (id: string) => `/api/v1/agents/${id}/deploy`,
    INVOKE: (id: string) => `/api/v1/agents/${id}/invoke`,
    HEALTH: (id: string) => `/api/v1/agents/${id}/health`,
    LOGS: (id: string) => `/api/v1/agents/${id}/logs`,
  },

  // Workflows
  WORKFLOWS: {
    BASE: '/api/v1/workflows',
    EXECUTE: (id: string) => `/api/v1/workflows/${id}/execute`,
    STATUS: (id: string) => `/api/v1/workflows/${id}/status`,
  },

  // Tools
  TOOLS: {
    BASE: '/api/v1/tools',
    DEPLOY: (id: string) => `/api/v1/tools/${id}/deploy`,
    MCP_REGISTER: '/api/v1/tools/mcp/register',
  },

  // Observability
  OBSERVABILITY: {
    TRANSACTIONS: '/api/v1/observability/transactions',
    SESSIONS: (id: string) => `/api/v1/observability/sessions/${id}`,
    METRICS: '/api/v1/observability/metrics',
    HEALTH: '/api/v1/observability/health',
    LLM_USAGE: '/api/v1/observability/llm-usage',
  },

  // Master Data
  MASTER_DATA: {
    SKILLS: '/api/v1/master-data/skills',
    CONSTRAINTS: '/api/v1/master-data/constraints',
    PROMPTS: '/api/v1/master-data/prompts',
    MODELS: '/api/v1/master-data/models',
    SECRETS: '/api/v1/master-data/secrets',
  },
}

// Utility functions
export const formatError = (error: any): string => {
  if (error.response?.data?.message) {
    return error.response.data.message
  }
  if (error.message) {
    return error.message
  }
  return 'An unexpected error occurred'
}

export const handleApiError = (error: any) => {
  const message = formatError(error)
  console.error('API Error:', error)
  return new Error(message)
}
