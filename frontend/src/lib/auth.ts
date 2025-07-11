import { useAppStore } from './store'

export interface User {
  id: string
  name: string
  email: string
  avatar?: string
}

export function useAuth() {
  const { user, setUser } = useAppStore()

  const login = async (email: string, password: string) => {
    try {
      // Mock authentication - replace with actual API call
      const mockUser: User = {
        id: '1',
        name: 'John Doe',
        email: email,
        avatar: 'https://via.placeholder.com/40',
      }
      setUser(mockUser)
      return mockUser
    } catch (error) {
      throw new Error('Login failed')
    }
  }

  const logout = () => {
    setUser(null)
  }

  const isAuthenticated = !!user

  return {
    user,
    login,
    logout,
    isAuthenticated,
  }
}
