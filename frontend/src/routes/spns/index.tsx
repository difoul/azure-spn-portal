import { createFileRoute, Link } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { SpnList } from '../../components/SpnList'
import { Spinner } from '../../components/ui/Spinner'
import { Button } from '../../components/ui/Button'
import { listSpns } from '../../api/spns'

export const Route = createFileRoute('/spns/')({
  component: SpnsPage,
})

function SpnsPage() {
  const { data: spns, isLoading, error, refetch } = useQuery({
    queryKey: ['spns'],
    queryFn: listSpns,
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">Service Principals</h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-0.5">
            Manage your Azure service principals.
          </p>
        </div>
        <Link to="/spns/new">
          <Button>New SPN</Button>
        </Link>
      </div>

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-4">
          <p className="text-sm text-red-700 dark:text-red-300">
            Failed to load service principals. {(error as Error).message}
          </p>
          <button
            onClick={() => void refetch()}
            className="text-sm text-red-600 dark:text-red-400 underline mt-1"
          >
            Try again
          </button>
        </div>
      )}

      {spns && <SpnList spns={spns} />}
    </div>
  )
}
