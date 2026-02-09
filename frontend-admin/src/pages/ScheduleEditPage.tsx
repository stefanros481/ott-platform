import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getChannels,
  getSchedule,
  createScheduleEntry,
  updateScheduleEntry,
  deleteScheduleEntry,
  type ScheduleEntry,
  type SchedulePayload,
} from '@/api/admin'
import DataTable, { type Column } from '@/components/DataTable'
import { useToast } from '@/components/Toast'

function todayString() {
  return new Date().toISOString().split('T')[0]!
}

const emptyEntry: Omit<SchedulePayload, 'channel_id'> = {
  title: '',
  synopsis: '',
  genre: '',
  start_time: '',
  end_time: '',
  age_rating: '',
  is_new: false,
}

export default function ScheduleEditPage() {
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const [channelId, setChannelId] = useState('')
  const [date, setDate] = useState(todayString())
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState(emptyEntry)

  const { data: channels = [] } = useQuery({
    queryKey: ['admin-channels'],
    queryFn: getChannels,
  })

  const { data: entries = [], isLoading } = useQuery({
    queryKey: ['admin-schedule', channelId, date],
    queryFn: () => getSchedule(channelId, date),
    enabled: !!channelId && !!date,
  })

  const sortedEntries = useMemo(
    () =>
      [...entries].sort(
        (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime(),
      ),
    [entries],
  )

  const saveMutation = useMutation({
    mutationFn: (payload: SchedulePayload) =>
      editingId
        ? updateScheduleEntry(editingId, payload)
        : createScheduleEntry(payload),
    onSuccess: () => {
      showToast(editingId ? 'Entry updated' : 'Entry created', 'success')
      queryClient.invalidateQueries({
        queryKey: ['admin-schedule', channelId, date],
      })
      resetForm()
    },
    onError: (err: Error) => {
      showToast(err.message || 'Failed to save schedule entry', 'error')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteScheduleEntry,
    onSuccess: () => {
      showToast('Entry deleted', 'success')
      queryClient.invalidateQueries({
        queryKey: ['admin-schedule', channelId, date],
      })
    },
    onError: (err: Error) => {
      showToast(err.message || 'Failed to delete entry', 'error')
    },
  })

  function resetForm() {
    setForm(emptyEntry)
    setEditingId(null)
    setShowForm(false)
  }

  function startEdit(entry: ScheduleEntry) {
    setEditingId(entry.id)
    setForm({
      title: entry.title,
      synopsis: entry.synopsis,
      genre: entry.genre,
      start_time: entry.start_time.slice(0, 16),
      end_time: entry.end_time.slice(0, 16),
      age_rating: entry.age_rating,
      is_new: entry.is_new,
    })
    setShowForm(true)
  }

  function handleDelete(entry: ScheduleEntry) {
    if (window.confirm(`Delete "${entry.title}" from schedule?`)) {
      deleteMutation.mutate(entry.id)
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.title.trim() || !channelId) return
    saveMutation.mutate({ ...form, channel_id: channelId })
  }

  function formatTime(iso: string) {
    return new Date(iso).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const columns: Column<ScheduleEntry>[] = [
    {
      header: 'Time',
      accessor: 'start_time',
      className: 'w-36',
      render: (row) => (
        <span className="text-xs text-gray-600">
          {formatTime(row.start_time)} - {formatTime(row.end_time)}
        </span>
      ),
    },
    {
      header: 'Title',
      accessor: 'title',
      render: (row) => (
        <div>
          <span className="font-medium text-gray-900">{row.title}</span>
          {row.is_new && (
            <span className="ml-2 inline-flex rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700">
              NEW
            </span>
          )}
        </div>
      ),
    },
    { header: 'Genre', accessor: 'genre' },
    { header: 'Rating', accessor: 'age_rating', className: 'w-20' },
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
        <h1 className="text-2xl font-bold text-gray-900">Schedule</h1>
        {channelId && (
          <button
            onClick={() => {
              resetForm()
              setShowForm(true)
            }}
            className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-indigo-700"
          >
            + Add Entry
          </button>
        )}
      </div>

      {/* Channel / Date selectors */}
      <div className="mb-6 flex flex-wrap gap-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Channel
          </label>
          <select
            value={channelId}
            onChange={(e) => setChannelId(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">Select channel...</option>
            {channels.map((ch) => (
              <option key={ch.id} value={ch.id}>
                {ch.channel_number} - {ch.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Date
          </label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Inline form */}
      {showForm && channelId && (
        <form
          onSubmit={handleSubmit}
          className="mb-6 rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
        >
          <h2 className="mb-4 text-lg font-semibold text-gray-900">
            {editingId ? 'Edit Entry' : 'New Schedule Entry'}
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                required
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
                Age Rating
              </label>
              <input
                type="text"
                value={form.age_rating}
                onChange={(e) => setForm({ ...form, age_rating: e.target.value })}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Start Time
              </label>
              <input
                type="datetime-local"
                value={form.start_time}
                onChange={(e) => setForm({ ...form, start_time: e.target.value })}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                End Time
              </label>
              <input
                type="datetime-local"
                value={form.end_time}
                onChange={(e) => setForm({ ...form, end_time: e.target.value })}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
            <div className="flex items-end">
              <label className="flex items-center gap-2 pb-2">
                <input
                  type="checkbox"
                  checked={form.is_new}
                  onChange={(e) => setForm({ ...form, is_new: e.target.checked })}
                  className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-sm font-medium text-gray-700">New Episode</span>
              </label>
            </div>
          </div>
          <div className="mt-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Synopsis
            </label>
            <textarea
              value={form.synopsis}
              onChange={(e) => setForm({ ...form, synopsis: e.target.value })}
              rows={2}
              className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
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

      {!channelId ? (
        <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
          <p className="text-sm text-gray-500">
            Select a channel above to view and manage its schedule.
          </p>
        </div>
      ) : (
        <DataTable
          columns={columns}
          data={sortedEntries}
          isLoading={isLoading}
        />
      )}
    </div>
  )
}
