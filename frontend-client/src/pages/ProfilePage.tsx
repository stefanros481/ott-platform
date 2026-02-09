import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { getProfiles, createProfile, type Profile } from '../api/auth'

export default function ProfilePage() {
  const { setActiveProfile } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [isKids, setIsKids] = useState(false)

  const { data: profiles, isLoading } = useQuery({
    queryKey: ['profiles'],
    queryFn: getProfiles,
  })

  const createMutation = useMutation({
    mutationFn: (payload: { name: string; is_kids?: boolean }) => createProfile(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profiles'] })
      setShowCreate(false)
      setNewName('')
      setIsKids(false)
    },
  })

  const handleSelectProfile = (profile: Profile) => {
    setActiveProfile(profile)
    navigate('/')
  }

  const handleCreateProfile = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newName.trim()) return
    createMutation.mutate({ name: newName.trim(), is_kids: isKids || undefined })
  }

  const avatarColors = [
    'bg-primary-500',
    'bg-emerald-500',
    'bg-amber-500',
    'bg-rose-500',
    'bg-cyan-500',
    'bg-violet-500',
  ]

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-surface">
      <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">Who's Watching?</h1>
      <p className="text-gray-400 mb-10">Select your profile</p>

      {isLoading ? (
        <div className="flex gap-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex flex-col items-center gap-3">
              <div className="w-24 h-24 sm:w-32 sm:h-32 rounded-xl bg-surface-overlay animate-pulse" />
              <div className="w-16 h-4 rounded bg-surface-overlay animate-pulse" />
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-wrap justify-center gap-6 max-w-3xl">
          {profiles?.map((profile, index) => (
            <button
              key={profile.id}
              onClick={() => handleSelectProfile(profile)}
              className="group flex flex-col items-center gap-3 focus:outline-none"
            >
              <div className={`w-24 h-24 sm:w-32 sm:h-32 rounded-xl ${avatarColors[index % avatarColors.length] ?? 'bg-primary-500'} flex items-center justify-center border-2 border-transparent group-hover:border-white group-focus-visible:border-primary-400 transition-all duration-200 group-hover:scale-105`}>
                {profile.avatar_url ? (
                  <img src={profile.avatar_url} alt={profile.name} className="w-full h-full object-cover rounded-xl" />
                ) : (
                  <span className="text-3xl sm:text-4xl font-bold text-white uppercase">
                    {profile.name.charAt(0)}
                  </span>
                )}
              </div>
              <span className="text-sm text-gray-400 group-hover:text-white transition-colors">
                {profile.name}
                {profile.is_kids && (
                  <span className="ml-1 text-xs text-amber-400">Kids</span>
                )}
              </span>
            </button>
          ))}

          {/* Add Profile */}
          <button
            onClick={() => setShowCreate(true)}
            className="group flex flex-col items-center gap-3 focus:outline-none"
          >
            <div className="w-24 h-24 sm:w-32 sm:h-32 rounded-xl bg-surface-overlay border-2 border-dashed border-white/20 flex items-center justify-center group-hover:border-white/50 group-focus-visible:border-primary-400 transition-all duration-200 group-hover:scale-105">
              <svg className="w-10 h-10 text-gray-500 group-hover:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
            </div>
            <span className="text-sm text-gray-500 group-hover:text-white transition-colors">Add Profile</span>
          </button>
        </div>
      )}

      {/* Create Profile Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
          <div className="bg-surface-raised rounded-xl p-6 w-full max-w-sm border border-white/10 shadow-2xl">
            <h2 className="text-xl font-bold text-white mb-4">Add Profile</h2>
            <form onSubmit={handleCreateProfile} className="space-y-4">
              <div>
                <label htmlFor="profileName" className="block text-sm font-medium text-gray-300 mb-1.5">
                  Name
                </label>
                <input
                  id="profileName"
                  type="text"
                  value={newName}
                  onChange={e => setNewName(e.target.value)}
                  required
                  autoFocus
                  maxLength={30}
                  className="w-full px-4 py-2.5 rounded-lg bg-surface-overlay border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
                  placeholder="Profile name"
                />
              </div>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isKids}
                  onChange={e => setIsKids(e.target.checked)}
                  className="w-4 h-4 rounded border-white/20 bg-surface-overlay text-primary-500 focus:ring-primary-500 focus:ring-offset-0"
                />
                <span className="text-sm text-gray-300">Kids profile</span>
              </label>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="flex-1 py-2.5 text-sm font-medium text-gray-300 bg-surface-overlay rounded-lg hover:bg-white/10 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending || !newName.trim()}
                  className="flex-1 py-2.5 text-sm font-semibold text-white bg-primary-500 rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Creating...' : 'Save'}
                </button>
              </div>
              {createMutation.isError && (
                <p className="text-sm text-red-400">Failed to create profile. Please try again.</p>
              )}
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
