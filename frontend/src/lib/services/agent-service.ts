import { apiClient, API_ENDPOINTS } from '../api-client'
import { Agent, SearchFilters, SortOptions } from '@/types'

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

  // Search agents
  static async searchAgents(query: string, filters?: SearchFilters) {
    return await apiClient.get<Agent[]>(API_ENDPOINTS.AGENTS.SEARCH, {
      params: { query, ...filters },
    })
  }

  // Semantic search
  static async semanticSearch(query: string, limit = 10) {
    return await apiClient.post<Agent[]>(API_ENDPOINTS.AGENTS.SEMANTIC_SEARCH, {
      query,
      limit,
    })
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

  // Invoke agent
  static async invokeAgent(id: string, input: any) {
    return await apiClient.post<any>(API_ENDPOINTS.AGENTS.INVOKE(id), { input })
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
}

// React Query hooks for agent operations
export const useAgentQueries = {
  // Keys
  all: ['agents'] as const,
  lists: () => [...useAgentQueries.all, 'list'] as const,
  list: (filters?: SearchFilters) => [...useAgentQueries.lists(), { filters }] as const,
  details: () => [...useAgentQueries.all, 'detail'] as const,
  detail: (id: string) => [...useAgentQueries.details(), id] as const,
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
