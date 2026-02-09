import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getChannels,
  createChannel,
  updateChannel,
  deleteChannel,
  type Channel,
  type ChannelPayload,
} from '@/api/admin'
import DataTable, { type Column } from '@/components/DataTable'
import { useToast } from '@/components/Toast'

const emptyChannel: ChannelPayload = {
  name: '',
  channel_number: 0,
  logo_url: '',
  genre: '',
  is_hd: true,
  hls_live_url: '',
}

export default function ChannelListPage() {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<ChannelPayload>(emptyChannel)

  const { data: channels = [], isLoading } = useQuery({
    queryKey: ['admin-channels'],
    queryFn: getChannels,
  })

  const saveMutation = useMutation({
    mutationFn: (payload: ChannelPayload) =>
      editingId ? updateChannel(editingId, payload) : createChannel(payload),
    onSuccess: () => {
      showToast(editingId ? 'Channel updated' : 'Channel created', 'success')
      queryClient.invalidateQueries({ queryKey: ['admin-channels'] })
      resetForm()
    },
    onError: (err: Error) => {
      showToast(err.message || 'Failed to save channel', 'error')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteChannel,
    onSuccess: () => {
      showToast('Channel deleted', 'success')
      queryClient.invalidateQueries({ queryKey: ['admin-channels'] })
    },
    onError: (err: Error) => {
      showToast(err.message || 'Failed to delete channel', 'error')
    },
  })

  function resetForm() {
    setForm(emptyChannel)
    setEditingId(null)
    setShowForm(false)
  }

  function startEdit(channel: Channel) {
    setEditingId(channel.id)
    setForm({
      name: channel.name,
      channel_number: channel.channel_number,
      logo_url: channel.logo_url,
      genre: channel.genre,
      is_hd: channel.is_hd,
      hls_live_url: channel.hls_live_url ?? '',
    })
    setShowForm(true)
  }

  function handleDelete(channel: Channel) {
    if (window.confirm(`Delete channel "${channel.name}"?`)) {
      deleteMutation.mutate(channel.id)
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.name.trim()) return
    saveMutation.mutate(form)
  }

  const columns: Column<Channel>[] = [
    { header: '#', accessor: 'channel_number', className: 'w-16' },
    {
      header: 'Name',
      accessor: 'name',
      render: (row) => (
        <div className="flex items-center gap-2">
          {row.logo_url ? (
            <img src={row.logo_url} alt="" className="h-6 w-6 rounded object-contain" />
          ) : null}
          <span className="font-medium text-gray-900">{row.name}</span>
        </div>
      ),
    },
    { header: 'Genre', accessor: 'genre' },
    {
      header: 'HD',
      accessor: 'is_hd',
      className: 'w-16',
      render: (row) => (
        <span
          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
            row.is_hd
              ? 'bg-green-50 text-green-700'
              : 'bg-gray-100 text-gray-500'
          }`}
        >
          {row.is_hd ? 'HD' : 'SD'}
        </span>
      ),
    },
    {
      header: 'Actions',
      accessor: 'id',
      className: 'w-32',
      render: (row) => (
        <div className="flex gap-2">
          <button
            onClick={() => startEdit(row)}
            className="rounded px-2 py-1 text-xs font-medium text-indigo-600 transition-colors hover:bg-indigo-50"
          >
            Edit
          </button>
          <button
            onClick={() => handleDelete(row)}
            className="rounded px-2 py-1 text-xs font-medium text-red-600 transition-colors hover:bg-red-50"
          >
            Delete
          </button>
        </div>
      ),
    },
  ]

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Channels</h1>
        <button
          onClick={() => {
            resetForm()
            setShowForm(true)
          }}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-indigo-700"
        >
          + Add Channel
        </button>
      </div>

      {/* Inline form */}
      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="mb-6 rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
        >
          <h2 className="mb-4 text-lg font-semibold text-gray-900">
            {editingId ? 'Edit Channel' : 'New Channel'}
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Channel Number
              </label>
              <input
                type="number"
                value={form.channel_number}
                onChange={(e) =>
                  setForm({ ...form, channel_number: parseInt(e.target.value) || 0 })
                }
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Genre
              </label>
              <input
                type="text"
                value={form.genre}
                onChange={(e) => setForm({ ...form, genre: e.target.value })}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Logo URL
              </label>
              <input
                type="text"
                value={form.logo_url}
                onChange={(e) => setForm({ ...form, logo_url: e.target.value })}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                HLS Live URL
              </label>
              <input
                type="text"
                value={form.hls_live_url}
                onChange={(e) => setForm({ ...form, hls_live_url: e.target.value })}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div className="flex items-end">
              <label className="flex items-center gap-2 pb-2">
                <input
                  type="checkbox"
                  checked={form.is_hd}
                  onChange={(e) => setForm({ ...form, is_hd: e.target.checked })}
                  className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-sm font-medium text-gray-700">HD Channel</span>
              </label>
            </div>
          </div>
          <div className="mt-4 flex gap-3">
            <button
              type="submit"
              disabled={saveMutation.isPending}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-indigo-700 disabled:opacity-60"
            >
              {saveMutation.isPending
                ? 'Saving...'
                : editingId
                  ? 'Update'
                  : 'Create'}
            </button>
            <button
              type="button"
              onClick={resetForm}
              className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <DataTable
        columns={columns}
        data={channels ?? []}
        isLoading={isLoading}
      />
    </div>
  )
}
