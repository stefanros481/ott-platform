import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getTitles, deleteTitle, type Title } from '@/api/admin'
import DataTable, { type Column } from '@/components/DataTable'
import { useToast } from '@/components/Toast'

export default function CatalogListPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const pageSize = 20

  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showToast } = useToast()

  const { data, isLoading } = useQuery({
    queryKey: ['admin-titles', page, pageSize, search],
    queryFn: () => getTitles(page, pageSize, search),
  })

  const deleteMutation = useMutation({
    mutationFn: deleteTitle,
    onSuccess: () => {
      showToast('Title deleted', 'success')
      queryClient.invalidateQueries({ queryKey: ['admin-titles'] })
    },
    onError: (err: Error) => {
      showToast(err.message || 'Failed to delete title', 'error')
    },
  })

  function handleDelete(id: string, title: string) {
    if (window.confirm(`Delete "${title}"? This cannot be undone.`)) {
      deleteMutation.mutate(id)
    }
  }

  function handleSearch() {
    setSearch(searchInput)
    setPage(1)
  }

  const columns: Column<Title>[] = [
    {
      header: 'Title',
      accessor: 'title',
      render: (row) => (
        <div className="flex items-center gap-3">
          {row.poster_url ? (
            <img
              src={row.poster_url}
              alt=""
              className="h-10 w-7 rounded object-cover"
            />
          ) : (
            <div className="flex h-10 w-7 items-center justify-center rounded bg-gray-100 text-xs text-gray-400">
              N/A
            </div>
          )}
          <div>
            <p className="font-medium text-gray-900">{row.title}</p>
            <p className="text-xs text-gray-500">{row.synopsis_short?.slice(0, 60)}</p>
          </div>
        </div>
      ),
    },
    {
      header: 'Type',
      accessor: 'title_type',
      render: (row) => (
        <span className="inline-flex rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium capitalize text-gray-700">
          {row.title_type}
        </span>
      ),
    },
    { header: 'Year', accessor: 'release_year' },
    { header: 'Rating', accessor: 'age_rating' },
    {
      header: 'Genres',
      accessor: 'genres',
      render: (row) => (
        <div className="flex flex-wrap gap-1">
          {(row.genres ?? []).map((g) => (
            <span
              key={g.id}
              className="inline-flex rounded-full bg-indigo-50 px-2 py-0.5 text-xs text-indigo-700"
            >
              {g.name}
            </span>
          ))}
        </div>
      ),
    },
    {
      header: 'Actions',
      accessor: 'id',
      className: 'w-32',
      render: (row) => (
        <div className="flex gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation()
              navigate(`/catalog/${row.id}/edit`)
            }}
            className="rounded px-2 py-1 text-xs font-medium text-indigo-600 transition-colors hover:bg-indigo-50"
          >
            Edit
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleDelete(row.id, row.title)
            }}
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
        <h1 className="text-2xl font-bold text-gray-900">Catalog</h1>
        <button
          onClick={() => navigate('/catalog/new')}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-indigo-700"
        >
          + Add Title
        </button>
      </div>

      {/* Search */}
      <div className="mb-4 flex gap-2">
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search titles..."
          className="w-full max-w-sm rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm placeholder:text-gray-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        <button
          onClick={handleSearch}
          className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50"
        >
          Search
        </button>
      </div>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        isLoading={isLoading}
        pagination={
          data
            ? {
                page: data.page,
                pageSize: data.page_size,
                total: data.total,
                onPageChange: setPage,
              }
            : undefined
        }
      />
    </div>
  )
}
