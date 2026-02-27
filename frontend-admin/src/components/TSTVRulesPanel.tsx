import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getTSTVRules, updateTSTVRules, type TSTVRules } from '@/api/admin'
import { useToast } from '@/components/Toast'

const CUTV_OPTIONS = [2, 6, 12, 24, 48, 72, 168]

function formatHours(hours: number): string {
  if (hours < 24) return `${hours}h`
  const days = hours / 24
  return days === 7 ? '7 days' : `${days}d`
}

export default function TSTVRulesPanel() {
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [savingId, setSavingId] = useState<string | null>(null)

  const { data: rules = [], isLoading } = useQuery({
    queryKey: ['admin-tstv-rules'],
    queryFn: getTSTVRules,
  })

  const updateMut = useMutation({
    mutationFn: ({ channelId, data }: { channelId: string; data: Partial<TSTVRules> }) =>
      updateTSTVRules(channelId, data),
    onSuccess: () => {
      showToast('TSTV rules updated', 'success')
      setSavingId(null)
      queryClient.invalidateQueries({ queryKey: ['admin-tstv-rules'] })
    },
    onError: (err: Error) => {
      showToast(err.message, 'error')
      setSavingId(null)
    },
  })

  function handleToggle(rule: TSTVRules, field: 'tstv_enabled' | 'startover_enabled' | 'catchup_enabled') {
    setSavingId(rule.channel_id)
    updateMut.mutate({
      channelId: rule.channel_id,
      data: { [field]: !rule[field] },
    })
  }

  function handleWindowChange(rule: TSTVRules, hours: number) {
    setSavingId(rule.channel_id)
    updateMut.mutate({
      channelId: rule.channel_id,
      data: { cutv_window_hours: hours },
    })
  }

  if (isLoading) {
    return <div className="py-8 text-center text-sm text-gray-500">Loading TSTV rules...</div>
  }

  if (rules.length === 0) {
    return (
      <div>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">TSTV Rules</h2>
        <p className="py-8 text-center text-sm text-gray-500">No channels configured.</p>
      </div>
    )
  }

  return (
    <div>
      <h2 className="mb-4 text-lg font-semibold text-gray-900">TSTV Rules</h2>
      <div className="overflow-hidden rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Channel</th>
              <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">TSTV</th>
              <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">Start Over</th>
              <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">Catch-Up</th>
              <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">CUTV Window</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {rules.map((rule) => {
              const isSaving = savingId === rule.channel_id && updateMut.isPending
              return (
                <tr key={rule.channel_id} className={isSaving ? 'opacity-60' : ''}>
                  <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                    {rule.channel_name}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-center">
                    <ToggleCheckbox
                      checked={rule.tstv_enabled}
                      disabled={isSaving}
                      onChange={() => handleToggle(rule, 'tstv_enabled')}
                    />
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-center">
                    <ToggleCheckbox
                      checked={rule.startover_enabled}
                      disabled={isSaving || !rule.tstv_enabled}
                      onChange={() => handleToggle(rule, 'startover_enabled')}
                    />
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-center">
                    <ToggleCheckbox
                      checked={rule.catchup_enabled}
                      disabled={isSaving || !rule.tstv_enabled}
                      onChange={() => handleToggle(rule, 'catchup_enabled')}
                    />
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-center">
                    <select
                      value={rule.cutv_window_hours}
                      disabled={isSaving || !rule.tstv_enabled}
                      onChange={(e) => handleWindowChange(rule, parseInt(e.target.value))}
                      className="rounded-md border border-gray-300 px-2 py-1 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
                    >
                      {CUTV_OPTIONS.map((h) => (
                        <option key={h} value={h}>
                          {formatHours(h)}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function ToggleCheckbox({
  checked,
  disabled,
  onChange,
}: {
  checked: boolean
  disabled: boolean
  onChange: () => void
}) {
  return (
    <input
      type="checkbox"
      checked={checked}
      disabled={disabled}
      onChange={onChange}
      className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 disabled:opacity-50"
    />
  )
}
