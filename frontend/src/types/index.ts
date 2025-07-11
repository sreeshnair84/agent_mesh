// Agent types
export interface Agent {
  id: string
  name: string
  description: string
  tags: string[]
  owner: string
  type: 'template' | 'custom'
  status: 'active' | 'inactive' | 'deploying' | 'error'
  healthStatus: 'healthy' | 'degraded' | 'unhealthy'
  created: Date
  lastUsed: Date
  usageCount: number
  rating: number
  favorites: number
  config: AgentConfig
  dns?: string
  healthCheckUrl?: string
  authToken?: string
}

export interface AgentConfig {
  prompt: string
  model: string
  tools: string[]
  skills: string[]
  constraints: string[]
  temperature?: number
  maxTokens?: number
  timeout?: number
}

export interface AgentTemplate {
  id: string
  name: string
  description: string
  category: string
  config: Partial<AgentConfig>
  requiredTools: string[]
  requiredSkills: string[]
}

// Workflow types
export interface Workflow {
  id: string
  name: string
  description: string
  agents: WorkflowAgent[]
  status: 'active' | 'inactive' | 'error'
  created: Date
  lastUsed: Date
  usageCount: number
  rating: number
}

export interface WorkflowAgent {
  id: string
  agentId: string
  sequence: number
  conditions?: WorkflowCondition[]
}

export interface WorkflowCondition {
  type: 'success' | 'failure' | 'custom'
  nextAgentId?: string
  expression?: string
}

// Tool types
export interface Tool {
  id: string
  name: string
  description: string
  type: 'mcp' | 'custom'
  config: ToolConfig
  status: 'active' | 'inactive' | 'error'
  created: Date
  usageCount: number
}

export interface ToolConfig {
  endpoint?: string
  auth?: ToolAuth
  parameters?: ToolParameter[]
  responseSchema?: any
}

export interface ToolAuth {
  type: 'none' | 'api-key' | 'oauth' | 'basic'
  config: Record<string, any>
}

export interface ToolParameter {
  name: string
  type: 'string' | 'number' | 'boolean' | 'array' | 'object'
  required: boolean
  description?: string
  default?: any
}

// Observability types
export interface Transaction {
  id: string
  sessionId: string
  traceId: string
  parentTraceId?: string
  type: 'agent' | 'workflow' | 'tool'
  entityId: string
  entityName: string
  userId: string
  startTime: Date
  endTime?: Date
  duration?: number
  status: 'running' | 'success' | 'error'
  inputData: any
  outputData?: any
  errorMessage?: string
  llmUsage?: LLMUsage
  metadata: Record<string, any>
}

export interface LLMUsage {
  model: string
  promptTokens: number
  completionTokens: number
  totalTokens: number
  cost: number
}

// Master Data types
export interface Skill {
  id: string
  name: string
  description: string
  category: string
  created: Date
  usageCount: number
}

export interface Constraint {
  id: string
  name: string
  description: string
  type: string
  config: Record<string, any>
  created: Date
  usageCount: number
}

export interface Prompt {
  id: string
  name: string
  content: string
  version: string
  description?: string
  tags: string[]
  created: Date
  usageCount: number
  rating: number
}

export interface Model {
  id: string
  name: string
  provider: string
  config: ModelConfig
  created: Date
  usageCount: number
  cost: number
}

export interface ModelConfig {
  endpoint: string
  apiKey: string
  maxTokens: number
  temperature: number
  [key: string]: any
}

export interface Secret {
  id: string
  key: string
  value: string
  environment: string
  description?: string
  created: Date
  lastUsed?: Date
}

// API Response types
export interface APIResponse<T> {
  data: T
  message: string
  success: boolean
  errors?: string[]
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    page: number
    limit: number
    total: number
    pages: number
  }
}

// Filter and Search types
export interface SearchFilters {
  query?: string
  tags?: string[]
  type?: string
  status?: string
  owner?: string
  dateRange?: {
    start: Date
    end: Date
  }
}

export interface SortOptions {
  field: string
  direction: 'asc' | 'desc'
}

// User types
export interface User {
  id: string
  email: string
  name: string
  avatar?: string
  role: 'admin' | 'user' | 'viewer'
  created: Date
  lastLogin?: Date
}

// Theme types
export interface Theme {
  name: string
  colors: {
    primary: string
    secondary: string
    accent: string
  }
}
