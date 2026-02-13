import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { profile, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-2 text-sm font-medium transition-colors ${
      isActive ? 'text-white' : 'text-gray-400 hover:text-white'
    }`

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-surface/80 backdrop-blur-md border-b border-white/5">
      <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Left: Brand */}
          <Link to="/" className="flex items-center gap-2 shrink-0">
            <div className="w-8 h-8 rounded-lg bg-primary-500 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" />
              </svg>
            </div>
            <span className="text-lg font-bold text-white hidden sm:block">OTT Platform</span>
          </Link>

          {/* Center: Navigation Links */}
          <div className="flex items-center gap-1">
            <NavLink to="/" end className={linkClass}>Home</NavLink>
            <NavLink to="/browse" className={linkClass}>Browse</NavLink>
            <NavLink to="/epg" className={linkClass}>EPG</NavLink>
            <NavLink to="/watchlist" className={linkClass}>My List</NavLink>
          </div>

          {/* Right: Search, Profile, Logout */}
          <div className="flex items-center gap-3">
            <Link
              to="/search"
              className="p-2 text-gray-400 hover:text-white transition-colors"
              aria-label="Search"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
              </svg>
            </Link>

            <Link
              to="/parental-controls"
              className="p-2 text-gray-400 hover:text-white transition-colors"
              aria-label="Parental Controls"
              title="Parental Controls"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.75c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.25-8.25-3.286Zm0 13.036h.008v.008H12v-.008Z" />
              </svg>
            </Link>

            {profile && (
              <Link to="/profiles" className="flex items-center gap-2 text-sm text-gray-300 hover:text-white transition-colors">
                <div className="w-7 h-7 rounded bg-primary-700 flex items-center justify-center text-xs font-bold uppercase">
                  {profile.name.charAt(0)}
                </div>
                <span className="hidden sm:block">{profile.name}</span>
              </Link>
            )}

            <button
              onClick={handleLogout}
              className="text-sm text-gray-400 hover:text-white transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}
