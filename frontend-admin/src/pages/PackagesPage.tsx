import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getPackages,
  createPackage,
  updatePackage,
  deletePackage,
  assignTitleToPackage,
  removeTitleFromPackage,
  getPackageTitles,
  getTitleOffers,
  createOffer,
  updateOffer,
  getTitles,
  type PackageResponse,
  type PackageCreate,
  type OfferResponse,
  type OfferCreate,
} from '@/api/admin'
import { useToast } from '@/components/Toast'

// ── Tier badge colour map ─────────────────────────────────────────────────────

const TIER_COLORS: Record<string, string> = {
  free: 'bg-gray-100 text-gray-700',
  basic: 'bg-blue-50 text-blue-700',
  standard: 'bg-indigo-50 text-indigo-700',
  premium: 'bg-purple-50 text-purple-700',
}

function TierBadge({ tier }: { tier: string }) {
  const cls = TIER_COLORS[tier.toLowerCase()] ?? 'bg-gray-100 text-gray-600'
  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${cls}`}>
      {tier}
    </span>
  )
}

// ── Format price helper ───────────────────────────────────────────────────────

function formatPrice(priceCents: number, currency: string): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.toUpperCase(),
  }).format(priceCents / 100)
}

// ── Package form ──────────────────────────────────────────────────────────────

interface PackageFormProps {
  initial?: Partial<PackageCreate & { id: string }>
  onSave: (data: PackageCreate) => void
  onCancel: () => void
  isSaving: boolean
}

function PackageForm({ initial, onSave, onCancel, isSaving }: PackageFormProps) {
  const [name, setName] = useState(initial?.name ?? '')
  const [description, setDescription] = useState(initial?.description ?? '')
  const [tier, setTier] = useState(initial?.tier ?? 'basic')
  const [maxStreams, setMaxStreams] = useState(String(initial?.max_streams ?? 1))
  const [price, setPrice] = useState(
    initial?.price_cents != null ? String(initial.price_cents / 100) : ''
  )
  const [currency, setCurrency] = useState(initial?.currency ?? 'USD')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const priceCents = price ? Math.round(parseFloat(price) * 100) : 0
    onSave({ name, description, tier, max_streams: Number(maxStreams) || 1, price_cents: priceCents, currency })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 border-t border-gray-200 pt-4">
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <label className="block text-xs font-medium text-gray-700 mb-1">Name *</label>
          <input
            required
            value={name}
            onChange={e => setName(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="e.g. Premium"
          />
        </div>
        <div className="col-span-2">
          <label className="block text-xs font-medium text-gray-700 mb-1">Description</label>
          <input
            value={description}
            onChange={e => setDescription(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="Optional description"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Tier</label>
          <select
            value={tier}
            onChange={e => setTier(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="free">Free</option>
            <option value="basic">Basic</option>
            <option value="standard">Standard</option>
            <option value="premium">Premium</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Max Streams</label>
          <input
            type="number"
            min={1}
            max={10}
            value={maxStreams}
            onChange={e => setMaxStreams(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Monthly Price</label>
          <input
            type="number"
            min={0}
            step="0.01"
            value={price}
            onChange={e => setPrice(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="9.99"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Currency</label>
          <select
            value={currency}
            onChange={e => setCurrency(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="USD">USD</option>
            <option value="EUR">EUR</option>
            <option value="GBP">GBP</option>
          </select>
        </div>
      </div>
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={isSaving}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60 transition-colors"
        >
          {isSaving ? 'Saving...' : 'Save Package'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

// ── Manage Titles panel ───────────────────────────────────────────────────────

interface ManageTitlesPanelProps {
  pkg: PackageResponse
}

function ManageTitlesPanel({ pkg }: ManageTitlesPanelProps) {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [showAddSearch, setShowAddSearch] = useState(false)

  const { data: packageTitles, isLoading: titlesLoading } = useQuery({
    queryKey: ['admin-package-titles', pkg.id],
    queryFn: () => getPackageTitles(pkg.id),
  })

  const { data: searchResults, isLoading: searchLoading } = useQuery({
    queryKey: ['admin-titles-search', search],
    queryFn: () => getTitles(1, 10, search),
    enabled: search.length > 1,
  })

  const assignedIds = new Set((packageTitles?.items ?? []).map(t => t.id))

  const assignMutation = useMutation({
    mutationFn: (titleId: string) => assignTitleToPackage(pkg.id, titleId),
    onSuccess: () => {
      showToast('Title added to package', 'success')
      queryClient.invalidateQueries({ queryKey: ['admin-packages'] })
      queryClient.invalidateQueries({ queryKey: ['admin-package-titles', pkg.id] })
    },
    onError: (err: Error) => showToast(err.message || 'Failed to add title', 'error'),
  })

  const removeMutation = useMutation({
    mutationFn: (titleId: string) => removeTitleFromPackage(pkg.id, titleId),
    onSuccess: () => {
      showToast('Title removed from package', 'success')
      queryClient.invalidateQueries({ queryKey: ['admin-packages'] })
      queryClient.invalidateQueries({ queryKey: ['admin-package-titles', pkg.id] })
    },
    onError: (err: Error) => showToast(err.message || 'Failed to remove title', 'error'),
  })

  const searchResults_ = (searchResults?.items ?? []).filter(t => !assignedIds.has(t.id))

  return (
    <div className="mt-4 border-t border-gray-100 pt-4 space-y-4">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">
          Titles ({packageTitles?.total ?? pkg.title_count})
        </h3>
        <button
          onClick={() => { setShowAddSearch(v => !v); setSearch(''); setSearchInput('') }}
          className="rounded px-2 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50 transition-colors"
        >
          {showAddSearch ? 'Cancel' : '+ Add Title'}
        </button>
      </div>

      {/* Add title search */}
      {showAddSearch && (
        <div>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={searchInput}
              onChange={e => setSearchInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && setSearch(searchInput)}
              placeholder="Search by title name..."
              autoFocus
              className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            <button
              onClick={() => setSearch(searchInput)}
              className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Search
            </button>
          </div>
          {search && (
            <div className="rounded-lg border border-gray-200 bg-gray-50">
              {searchLoading ? (
                <p className="p-3 text-sm text-gray-500">Searching...</p>
              ) : searchResults_.length === 0 ? (
                <p className="p-3 text-sm text-gray-500">
                  {searchResults?.items.length === 0 ? 'No titles found.' : 'All matching titles are already in this package.'}
                </p>
              ) : (
                <ul className="divide-y divide-gray-200 max-h-48 overflow-y-auto">
                  {searchResults_.map(t => (
                    <li key={t.id} className="flex items-center justify-between px-3 py-2">
                      <div className="min-w-0">
                        <p className="text-sm text-gray-800 truncate">{t.title}</p>
                        <p className="text-xs text-gray-400 capitalize">{t.title_type} · {t.release_year}</p>
                      </div>
                      <button
                        onClick={() => assignMutation.mutate(t.id)}
                        disabled={assignMutation.isPending}
                        className="ml-3 shrink-0 rounded px-2 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50 transition-colors disabled:opacity-50"
                      >
                        + Add
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      )}

      {/* Current titles list */}
      {titlesLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map(i => <div key={i} className="h-9 rounded bg-gray-100 animate-pulse" />)}
        </div>
      ) : (packageTitles?.items ?? []).length === 0 ? (
        <p className="text-sm text-gray-400 text-center py-4">No titles in this package yet.</p>
      ) : (
        <ul className="divide-y divide-gray-100 max-h-80 overflow-y-auto rounded-lg border border-gray-200">
          {(packageTitles?.items ?? []).map(t => (
            <li key={t.id} className="flex items-center justify-between px-3 py-2 hover:bg-gray-50">
              <div className="min-w-0">
                <p className="text-sm text-gray-800 truncate">{t.title}</p>
                <p className="text-xs text-gray-400 capitalize">{t.title_type} · {t.release_year}</p>
              </div>
              <button
                onClick={() => removeMutation.mutate(t.id)}
                disabled={removeMutation.isPending && removeMutation.variables === t.id}
                className="ml-3 shrink-0 rounded px-2 py-1 text-xs font-medium text-red-500 hover:bg-red-50 transition-colors disabled:opacity-50"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// ── Offers section ────────────────────────────────────────────────────────────

interface OffersSectionProps {
  titleId: string
  titleName: string
}

function OffersSection({ titleId, titleName }: OffersSectionProps) {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [showForm, setShowForm] = useState(false)
  const [offerType, setOfferType] = useState<'rent' | 'buy'>('rent')
  const [priceCents, setPriceCents] = useState('')
  const [currency, setCurrency] = useState('USD')
  const [rentalHours, setRentalHours] = useState('48')

  const { data: offers = [], isLoading } = useQuery({
    queryKey: ['admin-offers', titleId],
    queryFn: () => getTitleOffers(titleId),
  })

  const createMutation = useMutation({
    mutationFn: (data: OfferCreate) => createOffer(titleId, data),
    onSuccess: () => {
      showToast('Offer created', 'success')
      setShowForm(false)
      setPriceCents('')
      queryClient.invalidateQueries({ queryKey: ['admin-offers', titleId] })
    },
    onError: (err: Error) => showToast(err.message || 'Failed to create offer', 'error'),
  })

  const toggleMutation = useMutation({
    mutationFn: ({ offerId, isActive }: { offerId: string; isActive: boolean }) =>
      updateOffer(titleId, offerId, { is_active: isActive }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-offers', titleId] }),
    onError: (err: Error) => showToast(err.message || 'Failed to update offer', 'error'),
  })

  function handleCreateOffer(e: React.FormEvent) {
    e.preventDefault()
    const cents = Math.round(parseFloat(priceCents) * 100)
    if (isNaN(cents) || cents <= 0) {
      showToast('Enter a valid price', 'error')
      return
    }
    createMutation.mutate({
      offer_type: offerType,
      price_cents: cents,
      currency,
      rental_window_hours: offerType === 'rent' ? Number(rentalHours) || 48 : null,
    })
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-sm font-semibold text-gray-800 truncate max-w-[200px]" title={titleName}>
            {titleName}
          </p>
          <p className="text-xs text-gray-500">{offers.length} offer(s)</p>
        </div>
        <button
          onClick={() => setShowForm(v => !v)}
          className="rounded px-2 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50 transition-colors"
        >
          {showForm ? 'Cancel' : '+ Add Offer'}
        </button>
      </div>

      {/* Existing offers */}
      {isLoading ? (
        <p className="text-xs text-gray-400">Loading...</p>
      ) : (
        <ul className="space-y-1 mb-3">
          {offers.map((offer: OfferResponse) => (
            <li key={offer.id} className="flex items-center justify-between text-xs">
              <span className="text-gray-700">
                <span className={`font-medium mr-1 ${offer.offer_type === 'rent' ? 'text-blue-600' : 'text-purple-600'}`}>
                  {offer.offer_type === 'rent' ? 'Rent' : 'Buy'}
                </span>
                {formatPrice(offer.price_cents, offer.currency)}
                {offer.rental_window_hours && (
                  <span className="ml-1 text-gray-400">({offer.rental_window_hours}h)</span>
                )}
              </span>
              <button
                onClick={() => toggleMutation.mutate({ offerId: offer.id, isActive: !offer.is_active })}
                disabled={toggleMutation.isPending}
                className={`rounded-full px-2 py-0.5 text-[10px] font-medium transition-colors ${
                  offer.is_active
                    ? 'bg-green-100 text-green-700 hover:bg-red-50 hover:text-red-600'
                    : 'bg-gray-100 text-gray-500 hover:bg-green-50 hover:text-green-600'
                }`}
              >
                {offer.is_active ? 'Active' : 'Inactive'}
              </button>
            </li>
          ))}
          {offers.length === 0 && <li className="text-xs text-gray-400">No offers yet.</li>}
        </ul>
      )}

      {/* Create offer form */}
      {showForm && (
        <form onSubmit={handleCreateOffer} className="border-t border-gray-100 pt-3 space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
              <select
                value={offerType}
                onChange={e => setOfferType(e.target.value as 'rent' | 'buy')}
                className="w-full rounded border border-gray-300 px-2 py-1.5 text-xs focus:border-indigo-500 focus:outline-none"
              >
                <option value="rent">Rent</option>
                <option value="buy">Buy</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Currency</label>
              <select
                value={currency}
                onChange={e => setCurrency(e.target.value)}
                className="w-full rounded border border-gray-300 px-2 py-1.5 text-xs focus:border-indigo-500 focus:outline-none"
              >
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Price ($)</label>
              <input
                required
                type="number"
                min="0.01"
                step="0.01"
                value={priceCents}
                onChange={e => setPriceCents(e.target.value)}
                placeholder="3.99"
                className="w-full rounded border border-gray-300 px-2 py-1.5 text-xs focus:border-indigo-500 focus:outline-none"
              />
            </div>
            {offerType === 'rent' && (
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Window (hours)</label>
                <input
                  type="number"
                  min="1"
                  value={rentalHours}
                  onChange={e => setRentalHours(e.target.value)}
                  className="w-full rounded border border-gray-300 px-2 py-1.5 text-xs focus:border-indigo-500 focus:outline-none"
                />
              </div>
            )}
          </div>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="w-full rounded bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-60 transition-colors"
          >
            {createMutation.isPending ? 'Creating...' : 'Create Offer'}
          </button>
        </form>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

type ActiveTab = 'packages' | 'offers'

export default function PackagesPage() {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [activeTab, setActiveTab] = useState<ActiveTab>('packages')
  const [selectedPkg, setSelectedPkg] = useState<PackageResponse | null>(null)
  const [showNewPackageForm, setShowNewPackageForm] = useState(false)
  const [editingPkgId, setEditingPkgId] = useState<string | null>(null)

  // Offers tab — title search
  const [offersSearch, setOffersSearch] = useState('')
  const [offersSearchInput, setOffersSearchInput] = useState('')

  const { data: packages = [], isLoading: pkgsLoading } = useQuery({
    queryKey: ['admin-packages'],
    queryFn: getPackages,
  })

  const { data: offersTitles, isLoading: offersTitlesLoading } = useQuery({
    queryKey: ['admin-titles-offers', offersSearch],
    queryFn: () => getTitles(1, 20, offersSearch),
    enabled: activeTab === 'offers',
  })

  const createPkgMutation = useMutation({
    mutationFn: createPackage,
    onSuccess: () => {
      showToast('Package created', 'success')
      setShowNewPackageForm(false)
      queryClient.invalidateQueries({ queryKey: ['admin-packages'] })
    },
    onError: (err: Error) => showToast(err.message || 'Failed to create package', 'error'),
  })

  const updatePkgMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<PackageCreate> }) =>
      updatePackage(id, data),
    onSuccess: () => {
      showToast('Package updated', 'success')
      setEditingPkgId(null)
      queryClient.invalidateQueries({ queryKey: ['admin-packages'] })
    },
    onError: (err: Error) => showToast(err.message || 'Failed to update package', 'error'),
  })

  const deletePkgMutation = useMutation({
    mutationFn: deletePackage,
    onSuccess: () => {
      showToast('Package deleted', 'success')
      if (selectedPkg && deletePkgMutation.variables === selectedPkg.id) {
        setSelectedPkg(null)
      }
      queryClient.invalidateQueries({ queryKey: ['admin-packages'] })
    },
    onError: (err: Error) => showToast(err.message || 'Failed to delete package', 'error'),
  })

  function handleDeletePackage(pkg: PackageResponse) {
    const warning = pkg.title_count > 0
      ? `Delete "${pkg.name}"? It has ${pkg.title_count} title(s) assigned.`
      : `Delete "${pkg.name}"?`
    if (window.confirm(warning)) {
      deletePkgMutation.mutate(pkg.id)
    }
  }

  return (
    <div>
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Packages & Offers</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage subscription packages and per-title TVOD offers.
        </p>
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="-mb-px flex gap-6">
          {(['packages', 'offers'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-3 text-sm font-medium capitalize transition-colors border-b-2 ${
                activeTab === tab
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* ── Packages tab ─────────────────────────────────────── */}
      {activeTab === 'packages' && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Left: package list */}
          <div>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-base font-semibold text-gray-800">Subscription Packages</h2>
              <button
                onClick={() => { setShowNewPackageForm(v => !v); setEditingPkgId(null) }}
                className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 transition-colors"
              >
                {showNewPackageForm ? 'Cancel' : '+ New Package'}
              </button>
            </div>

            {/* New package form */}
            {showNewPackageForm && (
              <div className="mb-4 rounded-lg border border-indigo-200 bg-indigo-50 p-4">
                <h3 className="mb-3 text-sm font-semibold text-gray-700">New Package</h3>
                <PackageForm
                  onSave={data => createPkgMutation.mutate(data)}
                  onCancel={() => setShowNewPackageForm(false)}
                  isSaving={createPkgMutation.isPending}
                />
              </div>
            )}

            {/* Package list */}
            {pkgsLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-20 rounded-lg bg-gray-100 animate-pulse" />
                ))}
              </div>
            ) : packages.length === 0 ? (
              <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center">
                <p className="text-sm text-gray-500">No packages yet. Create one to get started.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {packages.map(pkg => (
                  <div
                    key={pkg.id}
                    className={`rounded-lg border p-4 cursor-pointer transition-colors ${
                      selectedPkg?.id === pkg.id
                        ? 'border-indigo-400 bg-indigo-50'
                        : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
                    }`}
                    onClick={() => {
                      setSelectedPkg(prev => prev?.id === pkg.id ? null : pkg)
                      setEditingPkgId(null)
                    }}
                  >
                    {editingPkgId === pkg.id ? (
                      <div onClick={e => e.stopPropagation()}>
                        <PackageForm
                          initial={pkg}
                          onSave={data => updatePkgMutation.mutate({ id: pkg.id, data })}
                          onCancel={() => setEditingPkgId(null)}
                          isSaving={updatePkgMutation.isPending}
                        />
                      </div>
                    ) : (
                      <div className="flex items-start justify-between">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <p className="font-medium text-gray-900 truncate">{pkg.name}</p>
                            <TierBadge tier={pkg.tier} />
                          </div>
                          {pkg.description && (
                            <p className="text-xs text-gray-500 truncate">{pkg.description}</p>
                          )}
                          <div className="mt-1 flex items-center gap-3 text-xs text-gray-500">
                            <span>{pkg.max_streams} stream{pkg.max_streams !== 1 ? 's' : ''}</span>
                            <span>{pkg.title_count} title{pkg.title_count !== 1 ? 's' : ''}</span>
                            {pkg.price_cents > 0 && (
                              <span className="font-medium text-gray-700">
                                {formatPrice(pkg.price_cents, pkg.currency)}/mo
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-1 ml-3 shrink-0">
                          <button
                            onClick={e => { e.stopPropagation(); setEditingPkgId(pkg.id); setSelectedPkg(null) }}
                            className="rounded px-2 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50 transition-colors"
                          >
                            Edit
                          </button>
                          <button
                            onClick={e => { e.stopPropagation(); handleDeletePackage(pkg) }}
                            className="rounded px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 transition-colors"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right: manage titles for selected package */}
          <div>
            {selectedPkg ? (
              <div className="rounded-lg border border-gray-200 bg-white p-4">
                <div className="flex items-center gap-2 mb-1">
                  <h2 className="text-base font-semibold text-gray-800">{selectedPkg.name}</h2>
                  <TierBadge tier={selectedPkg.tier} />
                </div>
                <p className="text-xs text-gray-500 mb-2">
                  {selectedPkg.max_streams} stream(s) · {selectedPkg.title_count} title(s) assigned
                </p>
                <ManageTitlesPanel pkg={selectedPkg} />
              </div>
            ) : (
              <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center">
                <p className="text-sm text-gray-500">Select a package to manage its titles.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Offers tab ───────────────────────────────────────── */}
      {activeTab === 'offers' && (
        <div>
          <div className="mb-4 flex items-center gap-3">
            <input
              type="text"
              value={offersSearchInput}
              onChange={e => setOffersSearchInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && setOffersSearch(offersSearchInput)}
              placeholder="Search titles to manage offers..."
              className="w-full max-w-sm rounded-lg border border-gray-300 px-3 py-2 text-sm placeholder:text-gray-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
            <button
              onClick={() => setOffersSearch(offersSearchInput)}
              className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Search
            </button>
          </div>

          {offersTitlesLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-40 rounded-lg bg-gray-100 animate-pulse" />
              ))}
            </div>
          ) : (offersTitles?.items ?? []).length === 0 ? (
            <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center">
              <p className="text-sm text-gray-500">
                {offersSearch ? 'No titles found. Try a different search.' : 'Search for a title to manage its TVOD offers.'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {(offersTitles?.items ?? []).map(t => (
                <OffersSection key={t.id} titleId={t.id} titleName={t.title} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
