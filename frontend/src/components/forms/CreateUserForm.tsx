'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/Badge'
import { CreateUserFormData } from '@/types/create-forms'
import { User, Shield, Mail, Eye, EyeOff } from 'lucide-react'

interface CreateUserFormProps {
  onSubmit: (data: CreateUserFormData) => void
  onCancel: () => void
  isLoading?: boolean
}

export default function CreateUserForm({
  onSubmit,
  onCancel,
  isLoading = false
}: CreateUserFormProps) {
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [confirmPassword, setConfirmPassword] = useState('')

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors }
  } = useForm<CreateUserFormData>({
    defaultValues: {
      role: 'viewer',
      preferences: {}
    }
  })

  const password = watch('password')
  const role = watch('role')

  const userRoles = [
    { value: 'admin', label: 'Administrator', description: 'Full system access' },
    { value: 'editor', label: 'Editor', description: 'Can create and edit resources' },
    { value: 'viewer', label: 'Viewer', description: 'Read-only access' }
  ]

  const validatePassword = (value: string) => {
    if (value.length < 8) return 'Password must be at least 8 characters'
    if (!/(?=.*[a-z])/.test(value)) return 'Password must contain at least one lowercase letter'
    if (!/(?=.*[A-Z])/.test(value)) return 'Password must contain at least one uppercase letter'
    if (!/(?=.*\d)/.test(value)) return 'Password must contain at least one number'
    if (!/(?=.*[!@#$%^&*])/.test(value)) return 'Password must contain at least one special character'
    return true
  }

  const validateConfirmPassword = (value: string) => {
    if (value !== password) return 'Passwords do not match'
    return true
  }

  const onFormSubmit = (data: CreateUserFormData) => {
    if (confirmPassword !== password) {
      alert('Passwords do not match')
      return
    }
    onSubmit(data)
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2 flex items-center gap-2">
          <User className="w-6 h-6 text-blue-600" />
          Create New User
        </h2>
        <p className="text-gray-600">Add a new user to the Agent Mesh system</p>
      </div>

      <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Mail className="w-5 h-5" />
            User Information
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="email">Email Address *</Label>
              <Input
                id="email"
                type="email"
                {...register('email', { 
                  required: 'Email is required',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: 'Invalid email address'
                  }
                })}
                placeholder="user@example.com"
              />
              {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>}
            </div>

            <div>
              <Label htmlFor="username">Username *</Label>
              <Input
                id="username"
                {...register('username', { 
                  required: 'Username is required',
                  minLength: {
                    value: 3,
                    message: 'Username must be at least 3 characters'
                  },
                  pattern: {
                    value: /^[a-zA-Z0-9_-]+$/,
                    message: 'Username can only contain letters, numbers, underscores, and dashes'
                  }
                })}
                placeholder="johndoe"
              />
              {errors.username && <p className="text-red-500 text-sm mt-1">{errors.username.message}</p>}
            </div>

            <div className="md:col-span-2">
              <Label htmlFor="full_name">Full Name *</Label>
              <Input
                id="full_name"
                {...register('full_name', { required: 'Full name is required' })}
                placeholder="John Doe"
              />
              {errors.full_name && <p className="text-red-500 text-sm mt-1">{errors.full_name.message}</p>}
            </div>

            <div>
              <Label htmlFor="role">Role *</Label>
              <Select
                id="role"
                {...register('role', { required: 'Role is required' })}
              >
                {userRoles.map(role => (
                  <option key={role.value} value={role.value}>
                    {role.label}
                  </option>
                ))}
              </Select>
              {errors.role && <p className="text-red-500 text-sm mt-1">{errors.role.message}</p>}
              <p className="text-sm text-gray-500 mt-1">
                {userRoles.find(r => r.value === role)?.description}
              </p>
            </div>

            <div>
              <Label htmlFor="avatar_url">Avatar URL (Optional)</Label>
              <Input
                id="avatar_url"
                type="url"
                {...register('avatar_url', {
                  pattern: {
                    value: /^https?:\/\/.+/,
                    message: 'Please enter a valid URL'
                  }
                })}
                placeholder="https://example.com/avatar.jpg"
              />
              {errors.avatar_url && <p className="text-red-500 text-sm mt-1">{errors.avatar_url.message}</p>}
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5" />
            Security Settings
          </h3>

          <div className="space-y-4">
            <div>
              <Label htmlFor="password">Password *</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  {...register('password', { validate: validatePassword })}
                  placeholder="Enter password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && <p className="text-red-500 text-sm mt-1">{errors.password.message}</p>}
            </div>

            <div>
              <Label htmlFor="confirm_password">Confirm Password *</Label>
              <div className="relative">
                <Input
                  id="confirm_password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {confirmPassword && password !== confirmPassword && (
                <p className="text-red-500 text-sm mt-1">Passwords do not match</p>
              )}
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium mb-2">Password Requirements:</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li className={`flex items-center ${password && password.length >= 8 ? 'text-green-600' : ''}`}>
                  <span className="w-2 h-2 rounded-full bg-current mr-2"></span>
                  At least 8 characters
                </li>
                <li className={`flex items-center ${password && /(?=.*[a-z])/.test(password) ? 'text-green-600' : ''}`}>
                  <span className="w-2 h-2 rounded-full bg-current mr-2"></span>
                  One lowercase letter
                </li>
                <li className={`flex items-center ${password && /(?=.*[A-Z])/.test(password) ? 'text-green-600' : ''}`}>
                  <span className="w-2 h-2 rounded-full bg-current mr-2"></span>
                  One uppercase letter
                </li>
                <li className={`flex items-center ${password && /(?=.*\d)/.test(password) ? 'text-green-600' : ''}`}>
                  <span className="w-2 h-2 rounded-full bg-current mr-2"></span>
                  One number
                </li>
                <li className={`flex items-center ${password && /(?=.*[!@#$%^&*])/.test(password) ? 'text-green-600' : ''}`}>
                  <span className="w-2 h-2 rounded-full bg-current mr-2"></span>
                  One special character (!@#$%^&*)
                </li>
              </ul>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Role Permissions</h3>
          <div className="space-y-3">
            {role === 'admin' && (
              <div className="bg-red-50 p-4 rounded-lg">
                <h4 className="font-medium text-red-800 mb-2">Administrator Permissions</h4>
                <div className="grid grid-cols-2 gap-2">
                  <Badge variant="destructive">Full System Access</Badge>
                  <Badge variant="destructive">User Management</Badge>
                  <Badge variant="destructive">Agent Management</Badge>
                  <Badge variant="destructive">Workflow Management</Badge>
                  <Badge variant="destructive">Tool Management</Badge>
                  <Badge variant="destructive">System Configuration</Badge>
                </div>
              </div>
            )}

            {role === 'editor' && (
              <div className="bg-yellow-50 p-4 rounded-lg">
                <h4 className="font-medium text-yellow-800 mb-2">Editor Permissions</h4>
                <div className="grid grid-cols-2 gap-2">
                  <Badge variant="secondary">Create Agents</Badge>
                  <Badge variant="secondary">Edit Agents</Badge>
                  <Badge variant="secondary">Create Workflows</Badge>
                  <Badge variant="secondary">Edit Workflows</Badge>
                  <Badge variant="secondary">Create Tools</Badge>
                  <Badge variant="secondary">Edit Tools</Badge>
                </div>
              </div>
            )}

            {role === 'viewer' && (
              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="font-medium text-green-800 mb-2">Viewer Permissions</h4>
                <div className="grid grid-cols-2 gap-2">
                  <Badge variant="outline">View Agents</Badge>
                  <Badge variant="outline">View Workflows</Badge>
                  <Badge variant="outline">View Tools</Badge>
                  <Badge variant="outline">View Reports</Badge>
                  <Badge variant="outline">Execute Workflows</Badge>
                  <Badge variant="outline">Use Tools</Badge>
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-4 pt-6 border-t">
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading || !confirmPassword || password !== confirmPassword}>
            {isLoading ? 'Creating...' : 'Create User'}
          </Button>
        </div>
      </form>
    </div>
  )
}
