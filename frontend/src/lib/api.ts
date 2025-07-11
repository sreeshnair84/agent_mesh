const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const OBSERVABILITY_URL = process.env.NEXT_PUBLIC_OBSERVABILITY_URL || 'http://localhost:8001'

class ApiClient {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  setToken(token: string) {
    this.token = token
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const headers = {
      'Content-Type': 'application/json',
      ...(this.token && { Authorization: `Bearer ${this.token}` }),
      ...options.headers,
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`)
    }

    return response.json()
  }

  // Agent APIs
  agents = {
    list: (params?: any) => this.request<any[]>('/api/v1/agents', { 
      method: 'GET',
      ...(params && { body: JSON.stringify(params) })
    }),
    search: (params: any) => this.request<any[]>('/api/v1/agents/search/semantic', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
    get: (id: string) => this.request<any>(`/api/v1/agents/${id}`),
    create: (data: any) => this.request<any>('/api/v1/agents', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    update: (id: string, data: any) => this.request<any>(`/api/v1/agents/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
    delete: (id: string) => this.request<void>(`/api/v1/agents/${id}`, {
      method: 'DELETE',
    }),
    deploy: (id: string) => this.request<any>(`/api/v1/agents/${id}/deploy`, {
      method: 'POST',
    }),
    invoke: (id: string, input: any) => this.request<any>(`/api/v1/agents/${id}/invoke`, {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  }

  // Workflow APIs
  workflows = {
    list: () => this.request<any[]>('/api/v1/workflows'),
    get: (id: string) => this.request<any>(`/api/v1/workflows/${id}`),
    create: (data: any) => this.request<any>('/api/v1/workflows', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    execute: (id: string, input: any) => this.request<any>(`/api/v1/workflows/${id}/execute`, {
      method: 'POST',
      body: JSON.stringify(input),
    }),
  }

  // Tool APIs
  tools = {
    list: () => this.request<any[]>('/api/v1/tools'),
    get: (id: string) => this.request<any>(`/api/v1/tools/${id}`),
    create: (data: any) => this.request<any>('/api/v1/tools', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  }

  // Template APIs
  templates = {
    getAgentTemplates: () => this.request<any[]>('/api/v1/templates/agents'),
    getToolTemplates: () => this.request<any[]>('/api/v1/templates/tools'),
  }

  // Model APIs
  models = {
    list: () => this.request<any[]>('/api/v1/models'),
  }

  // Master Data APIs
  masterData = {
    skills: {
      list: () => this.request<any[]>('/api/v1/master-data/skills'),
      create: (data: any) => this.request<any>('/api/v1/master-data/skills', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    },
    constraints: {
      list: () => this.request<any[]>('/api/v1/master-data/constraints'),
      create: (data: any) => this.request<any>('/api/v1/master-data/constraints', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    },
    prompts: {
      list: () => this.request<any[]>('/api/v1/master-data/prompts'),
      create: (data: any) => this.request<any>('/api/v1/master-data/prompts', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    },
    secrets: {
      list: () => this.request<any[]>('/api/v1/master-data/secrets'),
      create: (data: any) => this.request<any>('/api/v1/master-data/secrets', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    },
  }
}

export const api = new ApiClient(API_BASE_URL)
export const observabilityApi = new ApiClient(OBSERVABILITY_URL)
