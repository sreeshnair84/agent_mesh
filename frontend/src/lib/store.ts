import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  name: string
  email: string
  avatar?: string
}

interface AppState {
  user: User | null
  theme: string
  sidebarCollapsed: boolean
  setUser: (user: User | null) => void
  setTheme: (theme: string) => void
  setSidebarCollapsed: (collapsed: boolean) => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      user: null,
      theme: 'purple',
      sidebarCollapsed: false,
      setUser: (user) => set({ user }),
      setTheme: (theme) => set({ theme }),
      setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),
    }),
    {
      name: 'agent-mesh-storage',
    }
  )
)
