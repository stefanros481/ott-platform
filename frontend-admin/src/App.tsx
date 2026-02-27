import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import Sidebar from '@/components/Sidebar'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import CatalogListPage from '@/pages/CatalogListPage'
import CatalogEditPage from '@/pages/CatalogEditPage'
import ChannelListPage from '@/pages/ChannelListPage'
import ScheduleEditPage from '@/pages/ScheduleEditPage'
import UserListPage from '@/pages/UserListPage'
import PackagesPage from '@/pages/PackagesPage'
import AnalyticsPage from '@/pages/AnalyticsPage'
import StreamingPage from '@/pages/StreamingPage'

function AuthGuard() {
  const { isAuthenticated, isAdmin } = useAuth()

  if (!isAuthenticated || !isAdmin) {
    return <Navigate to="/login" replace />
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="ml-64 flex-1 p-6 lg:p-8">
        <Outlet />
      </main>
    </div>
  )
}

function PublicGuard() {
  const { isAuthenticated, isAdmin } = useAuth()

  if (isAuthenticated && isAdmin) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}

export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route element={<PublicGuard />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>

      {/* Protected admin routes */}
      <Route element={<AuthGuard />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/catalog" element={<CatalogListPage />} />
        <Route path="/catalog/new" element={<CatalogEditPage />} />
        <Route path="/catalog/:id/edit" element={<CatalogEditPage />} />
        <Route path="/channels" element={<ChannelListPage />} />
        <Route path="/schedule" element={<ScheduleEditPage />} />
        <Route path="/users" element={<UserListPage />} />
        <Route path="/packages" element={<PackagesPage />} />
        <Route path="/streaming" element={<StreamingPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
      </Route>

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
