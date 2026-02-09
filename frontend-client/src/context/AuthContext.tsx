import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'

interface User {
  id: string
  email: string
  subscription_tier: string
}

interface Profile {
  id: string
  name: string
  avatar_url: string | null
}

interface AuthState {
  user: User | null
  profile: Profile | null
  token: string | null
}

interface AuthContextType extends AuthState {
  login: (token: string, user: User) => void
  logout: () => void
  setActiveProfile: (profile: Profile) => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(() => {
    const token = localStorage.getItem('token')
    const user = localStorage.getItem('user')
    const profile = localStorage.getItem('profile')
    return {
      token,
      user: user ? JSON.parse(user) : null,
      profile: profile ? JSON.parse(profile) : null,
    }
  })

  const login = useCallback((token: string, user: User) => {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))
    setState(prev => ({ ...prev, token, user }))
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('profile')
    setState({ token: null, user: null, profile: null })
  }, [])

  const setActiveProfile = useCallback((profile: Profile) => {
    localStorage.setItem('profile', JSON.stringify(profile))
    setState(prev => ({ ...prev, profile }))
  }, [])

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        logout,
        setActiveProfile,
        isAuthenticated: !!state.token,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
