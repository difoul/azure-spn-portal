import { createFileRoute, Link, Outlet } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { getSpn } from '../../api/spns'
import { Spinner } from '../../components/ui/Spinner'
import { Badge } from '../../components/ui/Badge'

export const Route = createFileRoute('/spns/$spnId')({
  component: SpnDetailLayout,
})

function SpnDetailLayout() {
  const { spnId } = Route.useParams()

  const { data: spn, isLoading, error } = useQuery({
    queryKey: ['spns', spnId],
    queryFn: () => getSpn(spnId),
  })

  if (isLoading) return <div className="flex justify-center py-16"><Spinner /></div>

  if (error) return (
    <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-4">
      <p className="text-sm text-red-700 dark:text-red-300">Failed to load service principal.</p>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Link to="/spns" className="text-sm text-neutral-500 dark:text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200">
                Service Principals
              </Link>
              <span className="text-neutral-300 dark:text-neutral-600">/</span>
              <span className="text-sm text-neutral-700 dark:text-neutral-300">{spn?.displayName}</span>
            </div>
            <h1 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">{spn?.displayName}</h1>
            {spn?.description && (
              <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-0.5">{spn.description}</p>
            )}
          </div>
          {spn && (
            <div className="flex flex-col items-end gap-1 text-xs text-neutral-500 dark:text-neutral-400">
              <span className="font-mono">{spn.appId}</span>
              {spn.secretCount >= 2 && <Badge variant="yellow">Max secrets</Badge>}
            </div>
          )}
        </div>
      </div>

      {/* Tab bar */}
      <div className="border-b border-neutral-200 dark:border-neutral-700">
        <nav className="flex gap-6 -mb-px">
          <Link
            to="/spns/$spnId/secrets"
            params={{ spnId }}
            className="pb-3 text-sm border-b-2 border-transparent text-neutral-500 dark:text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200 hover:border-neutral-300 transition-colors"
            activeProps={{ className: 'pb-3 text-sm border-b-2 border-blue-600 dark:border-blue-400 text-blue-600 dark:text-blue-400 font-medium' }}
          >
            Secrets
          </Link>
          <Link
            to="/spns/$spnId/owners"
            params={{ spnId }}
            className="pb-3 text-sm border-b-2 border-transparent text-neutral-500 dark:text-neutral-400 hover:text-neutral-700 dark:hover:text-neutral-200 hover:border-neutral-300 transition-colors"
            activeProps={{ className: 'pb-3 text-sm border-b-2 border-blue-600 dark:border-blue-400 text-blue-600 dark:text-blue-400 font-medium' }}
          >
            Owners
          </Link>
        </nav>
      </div>

      <Outlet />
    </div>
  )
}
