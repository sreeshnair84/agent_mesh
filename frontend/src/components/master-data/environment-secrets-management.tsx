'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Plus, 
  Search, 
  Edit, 
  Trash2, 
  Eye, 
  EyeOff,
  Key,
  Lock,
  Globe,
  Shield,
  Copy,
  Check
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { SecretForm } from './secret-form'
import { apiClient } from '@/lib/api-client'

import { EnvironmentSecret } from './types'

const SECRET_CATEGORIES = {
  api_key: { label: 'API Key', color: 'bg-blue-100 text-blue-800', icon: Key },
  database: { label: 'Database', color: 'bg-green-100 text-green-800', icon: Lock },
  auth: { label: 'Authentication', color: 'bg-purple-100 text-purple-800', icon: Shield },
  service: { label: 'Service', color: 'bg-orange-100 text-orange-800', icon: Globe },
  webhook: { label: 'Webhook', color: 'bg-red-100 text-red-800', icon: Key },
  other: { label: 'Other', color: 'bg-gray-100 text-gray-800', icon: Key }
}

const ACCESS_LEVELS = {
  public: { label: 'Public', color: 'bg-gray-100 text-gray-800' },
  internal: { label: 'Internal', color: 'bg-blue-100 text-blue-800' },
  restricted: { label: 'Restricted', color: 'bg-yellow-100 text-yellow-800' },
  confidential: { label: 'Confidential', color: 'bg-red-100 text-red-800' }
}

interface EnvironmentSecretsManagementProps {
  selectionMode?: boolean
  selectedSecrets?: string[]
  onSecretSelect?: (secretId: string) => void
  onSecretDeselect?: (secretId: string) => void
  environment?: string
}

export default function EnvironmentSecretsManagement({
  selectionMode = false,
  selectedSecrets = [],
  onSecretSelect,
  onSecretDeselect,
  environment
}: EnvironmentSecretsManagementProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [selectedEnvironment, setSelectedEnvironment] = useState<string>(environment || '')
  const [selectedAccessLevel, setSelectedAccessLevel] = useState<string>('')
  const [showForm, setShowForm] = useState(false)
  const [editingSecret, setEditingSecret] = useState<EnvironmentSecret | null>(null)
  const [visibleSecrets, setVisibleSecrets] = useState<Set<string>>(new Set())
  const [copiedSecrets, setCopiedSecrets] = useState<Set<string>>(new Set())

  const queryClient = useQueryClient()

  const { data: secrets = [], isLoading } = useQuery({
    queryKey: ['environment-secrets'],
    queryFn: () => apiClient.get<EnvironmentSecret[]>('/api/v1/environment-secrets'),
    select: (data) => data.data || []
  })

  const { data: environments = [] } = useQuery({
    queryKey: ['environments'],
    queryFn: () => apiClient.get<string[]>('/api/v1/environments'),
    select: (data) => data.data || ['development', 'staging', 'production']
  })

  const createSecretMutation = useMutation({
    mutationFn: (secret: Omit<EnvironmentSecret, 'id' | 'createdAt' | 'updatedAt'>) =>
      apiClient.post('/api/v1/environment-secrets', secret),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['environment-secrets'] })
      setShowForm(false)
      setEditingSecret(null)
    }
  })

  const updateSecretMutation = useMutation({
    mutationFn: ({ id, ...secret }: Partial<EnvironmentSecret> & { id: string }) =>
      apiClient.put(`/api/v1/environment-secrets/${id}`, secret),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['environment-secrets'] })
      setShowForm(false)
      setEditingSecret(null)
    }
  })

  const deleteSecretMutation = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/api/v1/environment-secrets/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['environment-secrets'] })
    }
  })

  const filteredSecrets = secrets.filter(secret => {
    const matchesSearch = secret.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         secret.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         secret.key.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = !selectedCategory || secret.category === selectedCategory
    const matchesEnvironment = !selectedEnvironment || secret.environment === selectedEnvironment
    const matchesAccessLevel = !selectedAccessLevel || secret.accessLevel === selectedAccessLevel
    
    return matchesSearch && matchesCategory && matchesEnvironment && matchesAccessLevel
  })

  const handleSecretToggle = (secretId: string) => {
    if (selectedSecrets.includes(secretId)) {
      onSecretDeselect?.(secretId)
    } else {
      onSecretSelect?.(secretId)
    }
  }

  const toggleSecretVisibility = (secretId: string) => {
    setVisibleSecrets(prev => {
      const newSet = new Set(prev)
      if (newSet.has(secretId)) {
        newSet.delete(secretId)
      } else {
        newSet.add(secretId)
      }
      return newSet
    })
  }

  const copySecretValue = async (secret: EnvironmentSecret) => {
    try {
      await navigator.clipboard.writeText(secret.value)
      setCopiedSecrets(prev => new Set(Array.from(prev).concat(secret.id)))
      setTimeout(() => {
        setCopiedSecrets(prev => {
          const newSet = new Set(prev)
          newSet.delete(secret.id)
          return newSet
        })
      }, 2000)
    } catch (err) {
      console.error('Failed to copy secret value')
    }
  }

  const SecretCard = ({ secret }: { secret: EnvironmentSecret }) => {
    const category = SECRET_CATEGORIES[secret.category]
    const accessLevel = ACCESS_LEVELS[secret.accessLevel]
    const CategoryIcon = category.icon
    const isVisible = visibleSecrets.has(secret.id)
    const isCopied = copiedSecrets.has(secret.id)
    const isSelected = selectedSecrets.includes(secret.id)
    const isExpired = secret.expiresAt && new Date(secret.expiresAt) < new Date()

    return (
      <div 
        className={`border rounded-lg p-4 bg-white ${
          selectionMode 
            ? isSelected 
              ? 'ring-2 ring-purple-500 bg-purple-50' 
              : 'hover:bg-gray-50 cursor-pointer'
            : 'hover:shadow-md'
        } ${isExpired ? 'border-red-300 bg-red-50' : ''} transition-all duration-200`}
        onClick={selectionMode ? () => handleSecretToggle(secret.id) : undefined}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3 flex-1">
            <div className="flex-shrink-0">
              <CategoryIcon className="h-5 w-5 text-gray-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <h3 className="text-sm font-medium text-gray-900 truncate">
                  {secret.name}
                </h3>
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${category.color}`}>
                  {category.label}
                </span>
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${accessLevel.color}`}>
                  {accessLevel.label}
                </span>
                {isExpired && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                    Expired
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-500 mb-2">{secret.description}</p>
              <div className="flex items-center space-x-4 text-xs text-gray-500">
                <span>Environment: {secret.environment}</span>
                <span>Key: {secret.key}</span>
                <span>Version: {secret.version}</span>
                {secret.lastUsed && (
                  <span>Last used: {new Date(secret.lastUsed).toLocaleDateString()}</span>
                )}
              </div>
              <div className="mt-2 flex items-center space-x-2">
                <div className="flex items-center space-x-1 bg-gray-100 rounded px-2 py-1">
                  <span className="text-xs text-gray-600">Value:</span>
                  <span className="text-xs font-mono">
                    {isVisible ? secret.value : '••••••••'}
                  </span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    toggleSecretVisibility(secret.id)
                  }}
                  className="p-1 text-gray-400 hover:text-gray-600 rounded"
                >
                  {isVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    copySecretValue(secret)
                  }}
                  className="p-1 text-gray-400 hover:text-gray-600 rounded"
                >
                  {isCopied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                </button>
              </div>
              {secret.tags.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {secret.tags.map(tag => (
                    <span
                      key={tag}
                      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
          {!selectionMode && (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => {
                  setEditingSecret(secret)
                  setShowForm(true)
                }}
                className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
              >
                <Edit className="h-4 w-4" />
              </button>
              <button
                onClick={() => {
                  if (confirm('Are you sure you want to delete this secret?')) {
                    deleteSecretMutation.mutate(secret.id)
                  }
                }}
                className="p-2 text-red-400 hover:text-red-600 rounded-lg hover:bg-red-100"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Environment Secrets</h1>
          <p className="text-gray-600 mt-1">
            {selectionMode ? 'Select secrets to use in your configuration' : 'Manage secure environment variables and API keys'}
          </p>
        </div>
        {!selectionMode && (
          <Button
            onClick={() => setShowForm(true)}
            className="bg-purple-600 hover:bg-purple-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Secret
          </Button>
        )}
      </div>

      {/* Filters */}
      <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search secrets..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            suppressHydrationWarning={true}
          />
        </div>
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          <option value="">All Categories</option>
          {Object.entries(SECRET_CATEGORIES).map(([key, category]) => (
            <option key={key} value={key}>{category.label}</option>
          ))}
        </select>
        <select
          value={selectedEnvironment}
          onChange={(e) => setSelectedEnvironment(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          <option value="">All Environments</option>
          {environments.map(env => (
            <option key={env} value={env}>{env}</option>
          ))}
        </select>
        <select
          value={selectedAccessLevel}
          onChange={(e) => setSelectedAccessLevel(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        >
          <option value="">All Access Levels</option>
          {Object.entries(ACCESS_LEVELS).map(([key, level]) => (
            <option key={key} value={key}>{level.label}</option>
          ))}
        </select>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-2xl font-bold text-gray-900">{filteredSecrets.length}</div>
          <div className="text-sm text-gray-600">Total Secrets</div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-2xl font-bold text-blue-600">
            {filteredSecrets.filter(s => s.category === 'api_key').length}
          </div>
          <div className="text-sm text-gray-600">API Keys</div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-2xl font-bold text-red-600">
            {filteredSecrets.filter(s => s.accessLevel === 'confidential').length}
          </div>
          <div className="text-sm text-gray-600">Confidential</div>
        </div>
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-2xl font-bold text-yellow-600">
            {filteredSecrets.filter(s => s.expiresAt && new Date(s.expiresAt) < new Date()).length}
          </div>
          <div className="text-sm text-gray-600">Expired</div>
        </div>
      </div>

      {/* Secrets Grid */}
      <div className="grid grid-cols-1 gap-4">
        {filteredSecrets.map((secret) => (
          <SecretCard key={secret.id} secret={secret} />
        ))}
      </div>

      {filteredSecrets.length === 0 && (
        <div className="text-center py-12">
          <Key className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No secrets found</h3>
          <p className="text-gray-600">
            {searchTerm || selectedCategory || selectedEnvironment || selectedAccessLevel
              ? 'Try adjusting your filters to find what you\'re looking for.'
              : 'Get started by adding your first environment secret.'
            }
          </p>
        </div>
      )}

      {/* Form Modal */}
      <Modal
        isOpen={showForm}
        onClose={() => {
          setShowForm(false)
          setEditingSecret(null)
        }}
        title={editingSecret ? 'Edit Secret' : 'Add Secret'}
        size="lg"
      >
        <SecretForm
          secret={editingSecret}
          environments={environments}
          onSubmit={(secretData: any) => {
            if (editingSecret) {
              updateSecretMutation.mutate({ id: editingSecret.id, ...secretData })
            } else {
              createSecretMutation.mutate(secretData)
            }
          }}
          onCancel={() => {
            setShowForm(false)
            setEditingSecret(null)
          }}
          isLoading={createSecretMutation.isPending || updateSecretMutation.isPending}
        />
      </Modal>
    </div>
  )
}
