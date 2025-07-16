import { apiClient, API_ENDPOINTS } from '../api-client'
import { Agent, SearchFilters, SortOptions, AgentConfig, AgentTemplate } from '@/types'

export class AgentService {
  // Get all agents with optional filters
  static async getAgents(
    filters?: SearchFilters,
    sort?: SortOptions,
    page = 1,
    limit = 20
  ) {
    const params = {
      page,
      limit,
      ...filters,
      ...(sort && { sort_by: sort.field, sort_direction: sort.direction }),
    }

    return await apiClient.getPaginated<Agent>(API_ENDPOINTS.AGENTS.BASE, params)
  }

  // Get agent by ID
  static async getAgent(id: string) {
    return await apiClient.get<Agent>(`${API_ENDPOINTS.AGENTS.BASE}/${id}`)
  }

  // Create agent
  static async createAgent(agentData: Partial<Agent>) {
    return await apiClient.post<Agent>(API_ENDPOINTS.AGENTS.BASE, agentData)
  }

  // Update agent
  static async updateAgent(id: string, agentData: Partial<Agent>) {
    return await apiClient.put<Agent>(`${API_ENDPOINTS.AGENTS.BASE}/${id}`, agentData)
  }

  // Delete agent
  static async deleteAgent(id: string) {
    return await apiClient.delete<void>(`${API_ENDPOINTS.AGENTS.BASE}/${id}`)
  }

  // Deploy agent
  static async deployAgent(id: string) {
    return await apiClient.post<{ deployment_id: string }>(
      API_ENDPOINTS.AGENTS.DEPLOY(id)
    )
  }

  // Stop agent
  static async stopAgent(id: string) {
    return await apiClient.post<void>(API_ENDPOINTS.AGENTS.STOP(id))
  }

  // Restart agent
  static async restartAgent(id: string) {
    return await apiClient.post<void>(API_ENDPOINTS.AGENTS.RESTART(id))
  }

  // Scale agent
  static async scaleAgent(id: string, replicas: number) {
    return await apiClient.post<void>(API_ENDPOINTS.AGENTS.SCALE(id), { replicas })
  }

  // Rollback agent
  static async rollbackAgent(id: string, version?: string) {
    return await apiClient.post<void>(API_ENDPOINTS.AGENTS.ROLLBACK(id), { version })
  }

  // Chat with agent
  static async chatWithAgent(id: string, message: string, sessionId?: string) {
    return await apiClient.post<{ response: string; session_id: string }>(
      API_ENDPOINTS.AGENTS.CHAT(id), 
      { message, session_id: sessionId }
    )
  }

  // Get agent health
  static async getAgentHealth(id: string) {
    return await apiClient.get<{ status: string; details: any }>(
      API_ENDPOINTS.AGENTS.HEALTH(id)
    )
  }

  // Get agent logs
  static async getAgentLogs(id: string, limit = 100) {
    return await apiClient.get<string[]>(API_ENDPOINTS.AGENTS.LOGS(id), {
      params: { limit },
    })
  }

  // Get agent metrics
  static async getAgentMetrics(id: string) {
    return await apiClient.get<any>(API_ENDPOINTS.AGENTS.METRICS(id))
  }

  // Get agent config
  static async getAgentConfig(id: string) {
    return await apiClient.get<AgentConfig>(API_ENDPOINTS.AGENTS.CONFIG(id))
  }

  // Update agent config
  static async updateAgentConfig(id: string, config: Partial<AgentConfig>) {
    return await apiClient.put<AgentConfig>(API_ENDPOINTS.AGENTS.CONFIG(id), config)
  }

  // Get agent config versions
  static async getAgentConfigVersions(id: string) {
    return await apiClient.get<any[]>(API_ENDPOINTS.AGENTS.CONFIG_VERSIONS(id))
  }

  // Clone agent
  static async cloneAgent(id: string, name: string) {
    return await apiClient.post<Agent>(API_ENDPOINTS.AGENTS.CLONE(id), { name })
  }

  // Get agent categories
  static async getAgentCategories() {
    return await apiClient.get<string[]>(API_ENDPOINTS.AGENTS.CATEGORIES)
  }

  // Get agent templates
  static async getAgentTemplates() {
    return await apiClient.get<AgentTemplate[]>(API_ENDPOINTS.AGENTS.TEMPLATES)
  }

  // Create agent from template
  static async createAgentFromTemplate(templateId: string, name: string, config?: Partial<AgentConfig>) {
    return await apiClient.post<Agent>(API_ENDPOINTS.AGENTS.FROM_TEMPLATE, {
      template_id: templateId,
      name,
      config
    })
  }

  // Get agent payload specification
  static async getAgentPayload(id: string) {
    return await apiClient.get<any>(API_ENDPOINTS.AGENTS.PAYLOAD(id))
  }

  // Update agent payload specification
  static async updateAgentPayload(id: string, payload: any) {
    return await apiClient.put<any>(API_ENDPOINTS.AGENTS.PAYLOAD(id), payload)
  }
}

// React Query hooks for agent operations
export const useAgentQueries = {
  // Keys
  all: ['agents'] as const,
  lists: () => [...useAgentQueries.all, 'list'] as const,
  list: (filters?: SearchFilters) => [...useAgentQueries.lists(), { filters }] as const,
  details: () => [...useAgentQueries.all, 'detail'] as const,
  detail: (id: string) => [...useAgentQueries.details(), id] as const,
  categories: () => [...useAgentQueries.all, 'categories'] as const,
  templates: () => [...useAgentQueries.all, 'templates'] as const,
  health: (id: string) => [...useAgentQueries.detail(id), 'health'] as const,
  logs: (id: string) => [...useAgentQueries.detail(id), 'logs'] as const,
  metrics: (id: string) => [...useAgentQueries.detail(id), 'metrics'] as const,
  config: (id: string) => [...useAgentQueries.detail(id), 'config'] as const,
  payload: (id: string) => [...useAgentQueries.detail(id), 'payload'] as const,
}

// Example usage with React Query
/*
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export const useAgents = (filters?: SearchFilters) => {
  return useQuery({
    queryKey: useAgentQueries.list(filters),
    queryFn: () => AgentService.getAgents(filters),
  })
}

export const useAgent = (id: string) => {
  return useQuery({
    queryKey: useAgentQueries.detail(id),
    queryFn: () => AgentService.getAgent(id),
    enabled: !!id,
  })
}

export const useCreateAgent = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: AgentService.createAgent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: useAgentQueries.lists() })
    },
  })
}

export const useUpdateAgent = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Agent> }) =>
      AgentService.updateAgent(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: useAgentQueries.detail(id) })
      queryClient.invalidateQueries({ queryKey: useAgentQueries.lists() })
    },
  })
}

export const useDeleteAgent = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: AgentService.deleteAgent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: useAgentQueries.lists() })
    },
  })
}

export const useDeployAgent = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: AgentService.deployAgent,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: useAgentQueries.detail(id) })
    },
  })
}
*/
