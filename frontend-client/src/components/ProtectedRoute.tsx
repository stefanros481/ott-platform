import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireProfile?: boolean
}

export default function ProtectedRoute({ children, requireProfile = false }: ProtectedRouteProps) {
  const { isAuthenticated, profile } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (requireProfile && !profile) {
    return <Navigate to="/profiles" replace />
  }

  return <>{children}</>
}
