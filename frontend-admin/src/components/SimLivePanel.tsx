import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getSimLiveStatus,
  startSimLive,
  stopSimLive,
  restartSimLive,
  cleanupSimLive,
  type SimLiveChannelStatus,
} from '@/api/admin'
import { useToast } from '@/components/Toast'

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${units[i]}`
}

export default function SimLivePanel() {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const { data: channels = [], isLoading } = useQuery({
    queryKey: ['admin-simlive-status'],
    queryFn: getSimLiveStatus,
    refetchInterval: 10000,
  })

  const startMut = useMutation({
    mutationFn: startSimLive,
    onSuccess: (_, key) => {
      showToast(`Started ${key}`, 'success')
      queryClient.invalidateQueries({ queryKey: ['admin-simlive-status'] })
    },
    onError: (err: Error) => showToast(err.message, 'error'),
  })

  const stopMut = useMutation({
    mutationFn: stopSimLive,
    onSuccess: (_, key) => {
      showToast(`Stopped ${key}`, 'success')
      queryClient.invalidateQueries({ queryKey: ['admin-simlive-status'] })
    },
    onError: (err: Error) => showToast(err.message, 'error'),
  })

  const restartMut = useMutation({
    mutationFn: restartSimLive,
    onSuccess: (_, key) => {
      showToast(`Restarted ${key}`, 'success')
      queryClient.invalidateQueries({ queryKey: ['admin-simlive-status'] })
    },
    onError: (err: Error) => showToast(err.message, 'error'),
  })

  const cleanupMut = useMutation({
    mutationFn: cleanupSimLive,
    onSuccess: (result) => {
      showToast(
        `Cleaned ${result.total_segments_deleted} segments (${formatBytes(result.total_bytes_freed)})`,
        'success',
      )
      queryClient.invalidateQueries({ queryKey: ['admin-simlive-status'] })
    },
    onError: (err: Error) => showToast(err.message, 'error'),
  })

  const isBusy = startMut.isPending || stopMut.isPending || restartMut.isPending

  if (isLoading) {
    return <div className="py-8 text-center text-sm text-gray-500">Loading SimLive status...</div>
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">SimLive Channels</h2>
        <button
          onClick={() => cleanupMut.mutate()}
          disabled={cleanupMut.isPending}
          className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50 disabled:opacity-60"
        >
          {cleanupMut.isPending ? 'Cleaning...' : 'Cleanup Old Segments'}
        </button>
      </div>

      {channels.length === 0 ? (
        <p className="py-8 text-center text-sm text-gray-500">
          No SimLive channels configured. Start a channel to begin streaming.
        </p>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Channel</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">PID</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Segments</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Disk</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {channels.map((ch: SimLiveChannelStatus) => (
                <tr key={ch.channel_key}>
                  <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                    {ch.channel_key}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        ch.running
                          ? 'bg-green-50 text-green-700'
                          : ch.error
                            ? 'bg-red-50 text-red-700'
                            : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {ch.running ? 'Running' : ch.error ? 'Error' : 'Stopped'}
                    </span>
                    {ch.error && (
                      <p className="mt-1 text-xs text-red-600">{ch.error}</p>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                    {ch.pid ?? '—'}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                    {ch.segment_count}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                    {formatBytes(ch.disk_bytes)}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                    <div className="flex justify-end gap-2">
                      {ch.running ? (
                        <>
                          <button
                            onClick={() => restartMut.mutate(ch.channel_key)}
                            disabled={isBusy}
                            className="rounded px-2 py-1 text-xs font-medium text-amber-600 transition-colors hover:bg-amber-50 disabled:opacity-60"
                          >
                            Restart
                          </button>
                          <button
                            onClick={() => stopMut.mutate(ch.channel_key)}
                            disabled={isBusy}
                            className="rounded px-2 py-1 text-xs font-medium text-red-600 transition-colors hover:bg-red-50 disabled:opacity-60"
                          >
                            Stop
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => startMut.mutate(ch.channel_key)}
                          disabled={isBusy}
                          className="rounded px-2 py-1 text-xs font-medium text-green-600 transition-colors hover:bg-green-50 disabled:opacity-60"
                        >
                          Start
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
