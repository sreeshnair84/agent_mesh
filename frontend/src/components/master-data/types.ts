export interface EnvironmentSecret {
  id: string
  name: string
  description: string
  environment: string
  category: 'api_key' | 'database' | 'auth' | 'service' | 'webhook' | 'other'
  key: string
  value: string
  encrypted: boolean
  lastUsed?: Date
  createdAt: Date
  updatedAt: Date
  accessLevel: 'public' | 'internal' | 'restricted' | 'confidential'
  tags: string[]
  version: number
  expiresAt?: Date
}
