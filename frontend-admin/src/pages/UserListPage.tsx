import { useQuery } from '@tanstack/react-query'
import { getUsers, type AdminUser } from '@/api/admin'
import DataTable, { type Column } from '@/components/DataTable'

export default function UserListPage() {
  const { data: users = [], isLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: getUsers,
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
  ]

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Users</h1>
        <p className="mt-1 text-sm text-gray-500">
          Read-only view of registered users
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
