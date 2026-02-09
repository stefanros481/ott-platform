import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from 'react'
import type { User } from '@/api/admin'

interface AuthState {
  user: User | null
  token: string | null
}

interface AuthContextType extends AuthState {
  login: (token: string, refreshToken: string, user: User) => void
  logout: () => void
  isAuthenticated: boolean
  isAdmin: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(() => {
    const token = localStorage.getItem('token')
    const stored = localStorage.getItem('admin_user')
    return {
      token,
      user: stored ? (JSON.parse(stored) as User) : null,
    }
  })

  const login = useCallback(
    (token: string, refreshToken: string, user: User) => {
      localStorage.setItem('token', token)
      localStorage.setItem('refresh_token', refreshToken)
      localStorage.setItem('admin_user', JSON.stringify(user))
      setState({ token, user })
    },
    [],
  )

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('admin_user')
    setState({ token: null, user: null })
  }, [])

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        logout,
        isAuthenticated: !!state.token && !!state.user,
        isAdmin: !!state.user?.is_admin,
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
