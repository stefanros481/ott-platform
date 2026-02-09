import { Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Navbar from './components/Navbar'
import LoginPage from './pages/LoginPage'
import ProfilePage from './pages/ProfilePage'
import HomePage from './pages/HomePage'
import BrowsePage from './pages/BrowsePage'
import TitleDetailPage from './pages/TitleDetailPage'
import PlayerPage from './pages/PlayerPage'
import EpgPage from './pages/EpgPage'
import SearchPage from './pages/SearchPage'
import WatchlistPage from './pages/WatchlistPage'

/** Layout that includes the top navigation bar and page content below it. */
function AppLayout() {
  return (
    <>
      <Navbar />
      <main className="min-h-screen">
        <Outlet />
      </main>
    </>
  )
}

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<LoginPage />} />

        {/* Profile selection (authenticated but no navbar) */}
        <Route
          path="/profiles"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />

        {/* Player (full-screen, no navbar) */}
        <Route
          path="/play/:type/:id"
          element={
            <ProtectedRoute requireProfile>
              <PlayerPage />
            </ProtectedRoute>
          }
        />

        {/* Authenticated routes with navbar */}
        <Route
          element={
            <ProtectedRoute requireProfile>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<HomePage />} />
          <Route path="browse/:genre?" element={<BrowsePage />} />
          <Route path="title/:id" element={<TitleDetailPage />} />
          <Route path="epg" element={<EpgPage />} />
          <Route path="search" element={<SearchPage />} />
          <Route path="watchlist" element={<WatchlistPage />} />
        </Route>

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}

export default App
