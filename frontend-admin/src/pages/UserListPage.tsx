import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getUsers, getPackages, updateUserSubscription, getUserEntitlements, revokeUserEntitlement,
  type AdminUser, type PackageResponse, type UserEntitlement,
} from '@/api/admin'
import DataTable, { type Column } from '@/components/DataTable'
import { useToast } from '@/components/Toast'

// ── Helpers ────────────────────────────────────────────────────────────────────

const SOURCE_LABEL: Record<string, string> = {
  subscription: 'SVOD',
  tvod_rent: 'Rent',
  tvod_buy: 'Buy',
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { dateStyle: 'medium' })
}

// ── Subscription management modal ─────────────────────────────────────────────

interface ManageSubscriptionModalProps {
  user: AdminUser
  packages: PackageResponse[]
  onClose: () => void
}

function ManageSubscriptionModal({ user, packages, onClose }: ManageSubscriptionModalProps) {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [tab, setTab] = useState<'assign' | 'entitlements'>('entitlements')
  const [showExpired, setShowExpired] = useState(false)

  // Find current package by tier for pre-selection
  const currentPkg = packages.find(
    p => p.tier.toLowerCase() === user.subscription_tier?.toLowerCase()
      || p.name.toLowerCase() === user.subscription_tier?.toLowerCase(),
  )
  const [selectedPackageId, setSelectedPackageId] = useState<string>(currentPkg?.id ?? '')
  const [cancelSubscription, setCancelSubscription] = useState(false)

  const { data: entitlements = [], isLoading: entitlementsLoading } = useQuery({
    queryKey: ['admin-user-entitlements', user.id, showExpired],
    queryFn: () => getUserEntitlements(user.id, showExpired),
  })

  const assignMutation = useMutation({
    mutationFn: () => updateUserSubscription(user.id, cancelSubscription ? null : selectedPackageId || null),
    onSuccess: () => {
      showToast(cancelSubscription ? 'Subscription cancelled' : 'Subscription updated', 'success')
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
      queryClient.invalidateQueries({ queryKey: ['admin-user-entitlements', user.id] })
      setTab('entitlements')
    },
    onError: (err: Error) => showToast(err.message || 'Failed to update subscription', 'error'),
  })

  const revokeMutation = useMutation({
    mutationFn: (entitlementId: string) => revokeUserEntitlement(user.id, entitlementId),
    onSuccess: () => {
      showToast('Entitlement revoked', 'success')
      queryClient.invalidateQueries({ queryKey: ['admin-users'] })
      queryClient.invalidateQueries({ queryKey: ['admin-user-entitlements', user.id] })
    },
    onError: (err: Error) => showToast(err.message || 'Failed to revoke entitlement', 'error'),
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-lg rounded-xl border border-gray-200 bg-white shadow-2xl flex flex-col max-h-[90vh]">

        {/* Header */}
        <div className="flex items-start justify-between border-b border-gray-200 px-6 py-4 shrink-0">
          <div>
            <h2 className="text-base font-semibold text-gray-900">Manage Entitlements</h2>
            <p className="mt-0.5 text-sm text-gray-500 truncate">{user.email}</p>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 px-6 shrink-0">
          {(['entitlements', 'assign'] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`py-3 mr-6 text-sm font-medium border-b-2 transition-colors capitalize ${
                tab === t ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {t === 'assign' ? 'Assign Package' : 'Active Entitlements'}
            </button>
          ))}
        </div>

        {/* Body */}
        <div className="overflow-y-auto px-6 py-4 flex-1">

          {/* ── Entitlements tab ── */}
          {tab === 'entitlements' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-500">
                  {showExpired ? 'All entitlements (incl. expired)' : 'Active entitlements only'}
                </p>
                <button
                  onClick={() => setShowExpired(v => !v)}
                  className="text-xs text-indigo-600 hover:underline"
                >
                  {showExpired ? 'Hide expired' : 'Show history'}
                </button>
              </div>

              {entitlementsLoading ? (
                <div className="space-y-2">
                  {[1, 2].map(i => <div key={i} className="h-12 rounded-lg bg-gray-100 animate-pulse" />)}
                </div>
              ) : entitlements.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-6">No entitlements found.</p>
              ) : (
                <ul className="divide-y divide-gray-100 rounded-lg border border-gray-200">
                  {entitlements.map((ent: UserEntitlement) => (
                    <li key={ent.id} className={`flex items-start justify-between px-4 py-3 ${!ent.is_active ? 'opacity-50' : ''}`}>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${
                            ent.source_type === 'subscription'
                              ? 'bg-indigo-50 text-indigo-700'
                              : 'bg-amber-50 text-amber-700'
                          }`}>
                            {SOURCE_LABEL[ent.source_type] ?? ent.source_type}
                          </span>
                          <span className="text-sm font-medium text-gray-800 truncate">
                            {ent.package_name ?? ent.title_name ?? '—'}
                          </span>
                          {ent.package_tier && (
                            <span className="text-xs text-gray-400 capitalize">{ent.package_tier}</span>
                          )}
                        </div>
                        <p className="mt-0.5 text-xs text-gray-400">
                          Granted {formatDate(ent.granted_at)}
                          {ent.expires_at && ` · Expires ${formatDate(ent.expires_at)}`}
                          {!ent.is_active && ' · Expired'}
                        </p>
                      </div>
                      {ent.is_active && (
                        <button
                          onClick={() => revokeMutation.mutate(ent.id)}
                          disabled={revokeMutation.isPending && revokeMutation.variables === ent.id}
                          className="ml-3 shrink-0 rounded px-2 py-1 text-xs font-medium text-red-500 hover:bg-red-50 transition-colors disabled:opacity-50"
                        >
                          Revoke
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* ── Assign tab ── */}
          {tab === 'assign' && (
            <div className="space-y-4">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={cancelSubscription}
                  onChange={e => setCancelSubscription(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-sm text-gray-700">Cancel subscription (remove SVOD access)</span>
              </label>

              {!cancelSubscription && (
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Package</label>
                  {packages.length === 0 ? (
                    <p className="text-sm text-gray-400 italic">No packages configured yet.</p>
                  ) : (
                    <select
                      value={selectedPackageId}
                      onChange={e => setSelectedPackageId(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="">-- No package --</option>
                      {packages.map(pkg => (
                        <option key={pkg.id} value={pkg.id}>
                          {pkg.name} ({pkg.tier}) · {pkg.max_streams} stream(s)
                          {pkg.price_cents > 0 ? ` · $${(pkg.price_cents / 100).toFixed(2)}/mo` : ''}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              )}

              <div className="flex justify-end pt-2">
                <button
                  onClick={() => assignMutation.mutate()}
                  disabled={assignMutation.isPending}
                  className={`rounded-lg px-4 py-2 text-sm font-semibold text-white transition-colors disabled:opacity-60 ${
                    cancelSubscription ? 'bg-red-600 hover:bg-red-700' : 'bg-indigo-600 hover:bg-indigo-700'
                  }`}
                >
                  {assignMutation.isPending
                    ? 'Saving...'
                    : cancelSubscription ? 'Cancel Subscription' : 'Assign Package'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end border-t border-gray-200 px-6 py-4 shrink-0">
          <button
            onClick={onClose}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function UserListPage() {
  const [managingUser, setManagingUser] = useState<AdminUser | null>(null)

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: getUsers,
  })

  const { data: packages = [] } = useQuery({
    queryKey: ['admin-packages'],
    queryFn: getPackages,
  })

  const columns: Column<AdminUser>[] = [
    {
      header: 'Email',
      accessor: 'email',
      render: (row) => (
        <span className="font-medium text-gray-900">{row.email}</span>
      ),
    },
    {
      header: 'Tier',
      accessor: 'subscription_tier',
      render: (row) => (
        <span className="inline-flex rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium capitalize text-gray-700">
          {row.subscription_tier}
        </span>
      ),
    },
    {
      header: 'Admin',
      accessor: 'is_admin',
      className: 'w-20',
      render: (row) =>
        row.is_admin ? (
          <span className="inline-flex rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700">
            Admin
          </span>
        ) : (
          <span className="text-xs text-gray-400">-</span>
        ),
    },
    {
      header: 'Profiles',
      accessor: 'profiles_count',
      className: 'w-20',
      render: (row) => (
        <span className="text-sm text-gray-600">{row.profiles_count ?? '-'}</span>
      ),
    },
    {
      header: 'Created',
      accessor: 'created_at',
      render: (row) => (
        <span className="text-sm text-gray-500">
          {row.created_at
            ? new Date(row.created_at).toLocaleDateString()
            : '-'}
        </span>
      ),
    },
    {
      header: 'Actions',
      accessor: 'id',
      className: 'w-40',
      render: (row) => (
        <button
          onClick={(e) => {
            e.stopPropagation()
            setManagingUser(row)
          }}
          className="rounded px-2 py-1 text-xs font-medium text-indigo-600 transition-colors hover:bg-indigo-50"
        >
          Manage Subscription
        </button>
      ),
    },
  ]

  return (
    <div>
      {/* Subscription management modal */}
      {managingUser && (
        <ManageSubscriptionModal
          user={managingUser}
          packages={packages}
          onClose={() => setManagingUser(null)}
        />
      )}

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Users</h1>
        <p className="mt-1 text-sm text-gray-500">
          View registered users and manage their subscription packages.
        </p>
      </div>

      <DataTable
        columns={columns}
        data={users ?? []}
        isLoading={isLoading}
      />
    </div>
  )
}
