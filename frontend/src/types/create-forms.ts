// Types for create form components
export interface CreateAgentFormData {
  name: string
  display_name: string
  description: string
  category_id: string
  template_id?: string
  model_id: string
  system_prompt: string
  configuration: {
    temperature?: number
    max_tokens?: number
    timeout?: number
  }
  capabilities: string[]
  tools: string[]
  memory_config: {
    type: 'short_term' | 'long_term' | 'hybrid'
    max_size?: number
    persistence?: boolean
  }
  rate_limits: {
    requests_per_minute?: number
    requests_per_hour?: number
  }
  tags: string[]
}

export interface CreateSkillFormData {
  name: string
  description: string
  category: string
  config: Record<string, any>
  tags: string[]
  dependencies: string[]
  examples: string[]
}

export interface CreateToolFormData {
  name: string
  description: string
  type: 'api' | 'function' | 'database' | 'file' | 'webhook'
  category: string
  config: Record<string, any>
  schema_input: Record<string, any>
  schema_output: Record<string, any>
  endpoint_url?: string
  authentication: {
    type: 'none' | 'api_key' | 'oauth' | 'basic'
    config: Record<string, any>
  }
  rate_limits: {
    requests_per_minute?: number
    requests_per_hour?: number
  }
  timeout_seconds: number
  retries: number
}

export interface CreateWorkflowFormData {
  name: string
  description: string
  type: 'sequential' | 'parallel' | 'conditional' | 'crag'
  config: Record<string, any>
  agents: string[]
  tools: string[]
  steps: WorkflowStep[]
  triggers: WorkflowTrigger[]
}

export interface WorkflowStep {
  id: string
  name: string
  type: 'agent' | 'tool' | 'condition' | 'loop'
  config: Record<string, any>
  dependencies: string[]
  next_steps: string[]
}

export interface WorkflowTrigger {
  type: 'manual' | 'scheduled' | 'webhook' | 'event'
  config: Record<string, any>
}

export interface CreateUserFormData {
  email: string
  username: string
  full_name: string
  password: string
  role: 'admin' | 'editor' | 'viewer'
  avatar_url?: string
  preferences: Record<string, any>
}

export interface CreateAgentCategoryFormData {
  name: string
  display_name: string
  description: string
  icon: string
  color: string
  sort_order: number
}

export interface CreateAgentTemplateFormData {
  name: string
  display_name: string
  description: string
  template_type: 'crag' | 'supervisor' | 'plan_execute' | 'custom'
  category_id: string
  template_code: string
  config_schema: Record<string, any>
  default_config: Record<string, any>
  required_tools: string[]
  supported_models: string[]
  tags: string[]
}

export interface CreateLLMProviderFormData {
  name: string
  display_name: string
  provider_type: 'openai' | 'azure_openai' | 'anthropic' | 'google'
  api_endpoint?: string
  api_version?: string
  supported_models: string[]
  rate_limits: Record<string, any>
  configuration: Record<string, any>
}

export interface CreateModelConfigurationFormData {
  provider_id: string
  model_name: string
  display_name: string
  model_type: 'chat' | 'completion' | 'embedding' | 'image'
  max_tokens?: number
  context_length?: number
  supports_functions: boolean
  supports_streaming: boolean
  supports_vision: boolean
  pricing: Record<string, any>
  configuration: Record<string, any>
}

export interface CreatePromptFormData {
  name: string
  description: string
  category: string
  template: string
  variables: Record<string, any>
  tags: string[]
}

export interface CreateConstraintFormData {
  name: string
  description: string
  type: string
  config: Record<string, any>
  validation_rules: Record<string, any>
}

export interface CreateTemplateFormData {
  name: string
  description: string
  type: string
  category: string
  config: Record<string, any>
  schema_config: Record<string, any>
  default_values: Record<string, any>
  validation_rules: Record<string, any>
  tags: string[]
}

export interface CreateEnvironmentSecretFormData {
  name: string
  description: string
  value: string
  key_hint: string
}

export interface CreateAlertFormData {
  name: string
  description: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  conditions: Record<string, any>
  actions: Record<string, any>[]
}
