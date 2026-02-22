import { useState } from 'react'
import { Link } from '@tanstack/react-router'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Badge } from './ui/Badge'
import { Button } from './ui/Button'
import { ConfirmDialog } from './ConfirmDialog'
import { formatDate } from '../lib/utils'
import { deleteSpn } from '../api/spns'
import type { Spn } from '../api/types'

interface SpnListProps {
  spns: Spn[]
}

export function SpnList({ spns }: SpnListProps) {
  const queryClient = useQueryClient()
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteSpn(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['spns'] })
      setDeletingId(null)
    },
  })

  if (spns.length === 0) {
    return (
      <div className="text-center py-16 text-neutral-500 dark:text-neutral-400">
        <p className="text-sm">No service principals yet.</p>
        <p className="text-sm mt-1">
          <Link to="/spns/new" className="text-blue-600 dark:text-blue-400 hover:underline">
            Create your first SPN
          </Link>
        </p>
      </div>
    )
  }

  return (
    <>
      <div className="overflow-x-auto rounded-lg border border-neutral-200 dark:border-neutral-700">
        <table className="min-w-full divide-y divide-neutral-200 dark:divide-neutral-700">
          <thead className="bg-neutral-50 dark:bg-neutral-800">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                Name
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                App ID
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                Secrets
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                Created
              </th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200 dark:divide-neutral-700 bg-white dark:bg-neutral-900">
            {spns.map(spn => (
              <tr key={spn.id} className="hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors">
                <td className="px-4 py-3">
                  <Link
                    to="/spns/$spnId/secrets"
                    params={{ spnId: spn.id }}
                    className="font-medium text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    {spn.displayName}
                  </Link>
                  {spn.description && (
                    <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-0.5">{spn.description}</p>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-neutral-600 dark:text-neutral-400 font-mono">
                  {spn.appId}
                </td>
                <td className="px-4 py-3">
                  <Badge variant={spn.secretCount >= 2 ? 'yellow' : 'neutral'}>
                    {spn.secretCount} / 2
                  </Badge>
                </td>
                <td className="px-4 py-3 text-sm text-neutral-600 dark:text-neutral-400">
                  {formatDate(spn.createdAt)}
                </td>
                <td className="px-4 py-3 text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                    onClick={() => setDeletingId(spn.id)}
                  >
                    Delete
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {deletingId && (
        <ConfirmDialog
          title="Delete Service Principal"
          message={`Are you sure you want to delete "${spns.find(s => s.id === deletingId)?.displayName}"? This action cannot be undone.`}
          onConfirm={() => deleteMutation.mutate(deletingId)}
          onCancel={() => setDeletingId(null)}
          loading={deleteMutation.isPending}
        />
      )}
    </>
  )
}
