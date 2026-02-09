import { useState, useEffect, type FormEvent } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getTitle,
  createTitle,
  updateTitle,
  getGenres,
  type TitlePayload,
} from '@/api/admin'
import FormField from '@/components/FormField'
import { useToast } from '@/components/Toast'

const AGE_RATINGS = ['G', 'PG', 'PG-13', 'R', 'NC-17', 'TV-Y', 'TV-G', 'TV-PG', 'TV-14', 'TV-MA']

const emptyForm: TitlePayload = {
  title: '',
  title_type: 'movie',
  synopsis_short: '',
  synopsis_long: '',
  release_year: new Date().getFullYear(),
  duration_minutes: 0,
  age_rating: '',
  poster_url: '',
  landscape_url: '',
  hls_manifest_url: '',
  mood_tags: [],
  theme_tags: [],
  genre_ids: [],
}

export default function CatalogEditPage() {
  const { id } = useParams()
  const isEditing = !!id
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const [form, setForm] = useState<TitlePayload>(emptyForm)
  const [moodInput, setMoodInput] = useState('')
  const [themeInput, setThemeInput] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})

  const { data: existingTitle, isLoading: titleLoading } = useQuery({
    queryKey: ['admin-title', id],
    queryFn: () => getTitle(id!),
    enabled: isEditing,
  })

  const { data: genres = [] } = useQuery({
    queryKey: ['genres'],
    queryFn: getGenres,
  })

  useEffect(() => {
    if (existingTitle) {
      setForm({
        title: existingTitle.title,
        title_type: existingTitle.title_type,
        synopsis_short: existingTitle.synopsis_short,
        synopsis_long: existingTitle.synopsis_long,
        release_year: existingTitle.release_year,
        duration_minutes: existingTitle.duration_minutes,
        age_rating: existingTitle.age_rating,
        poster_url: existingTitle.poster_url,
        landscape_url: existingTitle.landscape_url,
        hls_manifest_url: existingTitle.hls_manifest_url,
        mood_tags: existingTitle.mood_tags ?? [],
        theme_tags: existingTitle.theme_tags ?? [],
        genre_ids: existingTitle.genre_ids ?? [],
      })
      setMoodInput((existingTitle.mood_tags ?? []).join(', '))
      setThemeInput((existingTitle.theme_tags ?? []).join(', '))
    }
  }, [existingTitle])

  const saveMutation = useMutation({
    mutationFn: (payload: TitlePayload) =>
      isEditing ? updateTitle(id!, payload) : createTitle(payload),
    onSuccess: () => {
      showToast(
        isEditing ? 'Title updated' : 'Title created',
        'success',
      )
      queryClient.invalidateQueries({ queryKey: ['admin-titles'] })
      queryClient.invalidateQueries({ queryKey: ['admin-title', id] })
      navigate('/catalog')
    },
    onError: (err: Error) => {
      showToast(err.message || 'Failed to save title', 'error')
    },
  })

  function update(field: keyof TitlePayload, value: unknown) {
    setForm((prev) => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev }
        delete next[field]
        return next
      })
    }
  }

  function validate(): boolean {
    const newErrors: Record<string, string> = {}
    if (!form.title.trim()) newErrors.title = 'Title is required'
    if (!form.title_type) newErrors.title_type = 'Type is required'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!validate()) return

    const payload: TitlePayload = {
      ...form,
      mood_tags: moodInput
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean),
      theme_tags: themeInput
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean),
    }

    saveMutation.mutate(payload)
  }

  if (isEditing && titleLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-indigo-600" />
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">
          {isEditing ? 'Edit Title' : 'Add New Title'}
        </h1>
      </div>

      <form
        onSubmit={handleSubmit}
        className="max-w-2xl space-y-5 rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
      >
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <FormField
            label="Title"
            name="title"
            type="text"
            value={form.title}
            onChange={(v) => update('title', v)}
            error={errors.title}
            required
          />
          <FormField
            label="Type"
            name="title_type"
            type="select"
            value={form.title_type}
            onChange={(v) => update('title_type', v)}
            options={[
              { value: 'movie', label: 'Movie' },
              { value: 'series', label: 'Series' },
            ]}
            error={errors.title_type}
            required
          />
        </div>

        <FormField
          label="Short Synopsis"
          name="synopsis_short"
          type="textarea"
          value={form.synopsis_short}
          onChange={(v) => update('synopsis_short', v)}
          rows={2}
        />

        <FormField
          label="Long Synopsis"
          name="synopsis_long"
          type="textarea"
          value={form.synopsis_long}
          onChange={(v) => update('synopsis_long', v)}
          rows={4}
        />

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          <FormField
            label="Release Year"
            name="release_year"
            type="number"
            value={form.release_year}
            onChange={(v) => update('release_year', parseInt(v) || 0)}
          />
          <FormField
            label="Duration (min)"
            name="duration_minutes"
            type="number"
            value={form.duration_minutes}
            onChange={(v) => update('duration_minutes', parseInt(v) || 0)}
          />
          <FormField
            label="Age Rating"
            name="age_rating"
            type="select"
            value={form.age_rating}
            onChange={(v) => update('age_rating', v)}
            options={AGE_RATINGS.map((r) => ({ value: r, label: r }))}
          />
        </div>

        <FormField
          label="Poster URL"
          name="poster_url"
          type="text"
          value={form.poster_url}
          onChange={(v) => update('poster_url', v)}
          placeholder="https://..."
        />

        <FormField
          label="Landscape Image URL"
          name="landscape_url"
          type="text"
          value={form.landscape_url}
          onChange={(v) => update('landscape_url', v)}
          placeholder="https://..."
        />

        <FormField
          label="HLS Manifest URL"
          name="hls_manifest_url"
          type="text"
          value={form.hls_manifest_url}
          onChange={(v) => update('hls_manifest_url', v)}
          placeholder="https://..."
        />

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Mood Tags
          </label>
          <input
            type="text"
            value={moodInput}
            onChange={(e) => setMoodInput(e.target.value)}
            placeholder="e.g. thrilling, dark, suspenseful"
            className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm placeholder:text-gray-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          <p className="mt-1 text-xs text-gray-400">Comma-separated</p>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Theme Tags
          </label>
          <input
            type="text"
            value={themeInput}
            onChange={(e) => setThemeInput(e.target.value)}
            placeholder="e.g. revenge, family, coming-of-age"
            className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm placeholder:text-gray-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          <p className="mt-1 text-xs text-gray-400">Comma-separated</p>
        </div>

        <FormField
          label="Genres"
          name="genre_ids"
          type="multiselect"
          value={form.genre_ids}
          onChange={(v) => update('genre_ids', v)}
          options={genres.map((g) => ({ value: g.id, label: g.name }))}
        />

        {/* Actions */}
        <div className="flex gap-3 border-t border-gray-200 pt-5">
          <button
            type="submit"
            disabled={saveMutation.isPending}
            className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {saveMutation.isPending ? 'Saving...' : isEditing ? 'Update Title' : 'Create Title'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/catalog')}
            className="rounded-lg border border-gray-300 bg-white px-5 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
