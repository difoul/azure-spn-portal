import { useState } from 'react'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { Button } from './ui/Button'
import { Input } from './ui/Input'
import { ConfirmDialog } from './ConfirmDialog'
import { Spinner } from './ui/Spinner'
import { listOwners, addOwner, removeOwner } from '../api/owners'

interface OwnerListProps {
  spnId: string
  currentUserOid: string
}

export function OwnerList({ spnId, currentUserOid }: OwnerListProps) {
  const queryClient = useQueryClient()
  const [removingId, setRemovingId] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newUpn, setNewUpn] = useState('')

  const { data: owners, isLoading, error } = useQuery({
    queryKey: ['spns', spnId, 'owners'],
    queryFn: () => listOwners(spnId),
  })

  const addMutation = useMutation({
    mutationFn: () => addOwner(spnId, { upn: newUpn.trim() }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['spns', spnId, 'owners'] })
      setShowAddForm(false)
      setNewUpn('')
    },
  })

  const removeMutation = useMutation({
    mutationFn: (ownerId: string) => removeOwner(spnId, ownerId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['spns', spnId, 'owners'] })
      setRemovingId(null)
    },
  })

  if (isLoading) return <div className="flex justify-center py-8"><Spinner /></div>
  if (error) return <p className="text-red-500 text-sm">Failed to load owners.</p>

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300">
          Owners ({owners?.length ?? 0})
        </h3>
        {!showAddForm && (
          <Button size="sm" onClick={() => setShowAddForm(true)}>
            Add owner
          </Button>
        )}
      </div>

      {showAddForm && (
        <form
          className="rounded-lg border border-neutral-200 dark:border-neutral-700 p-4 space-y-3"
          onSubmit={e => { e.preventDefault(); addMutation.mutate() }}
        >
          <Input
            label="User Principal Name (UPN)"
            type="email"
            value={newUpn}
            onChange={e => setNewUpn(e.target.value)}
            placeholder="user@company.com"
            required
            autoFocus
          />
          {addMutation.error && (
            <p className="text-sm text-red-500">{(addMutation.error as Error).message}</p>
          )}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" size="sm" onClick={() => setShowAddForm(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" loading={addMutation.isPending} disabled={!newUpn.trim()}>
              Add
            </Button>
          </div>
        </form>
      )}

      {owners && owners.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-neutral-200 dark:border-neutral-700">
          <table className="min-w-full divide-y divide-neutral-200 dark:divide-neutral-700">
            <thead className="bg-neutral-50 dark:bg-neutral-800">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">UPN</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-200 dark:divide-neutral-700 bg-white dark:bg-neutral-900">
              {owners.map(owner => (
                <tr key={owner.id} className="hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors">
                  <td className="px-4 py-3 text-sm text-neutral-900 dark:text-neutral-100">{owner.displayName}</td>
                  <td className="px-4 py-3 text-sm text-neutral-600 dark:text-neutral-400">{owner.upn}</td>
                  <td className="px-4 py-3 text-right">
                    {owner.id !== currentUserOid && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                        onClick={() => setRemovingId(owner.id)}
                      >
                        Remove
                      </Button>
                    )}
                    {owner.id === currentUserOid && (
                      <span className="text-xs text-neutral-400 dark:text-neutral-500 px-3">You</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {removingId && (
        <ConfirmDialog
          title="Remove Owner"
          message={`Remove "${owners?.find(o => o.id === removingId)?.displayName}" as an owner?`}
          confirmLabel="Remove"
          onConfirm={() => removeMutation.mutate(removingId)}
          onCancel={() => setRemovingId(null)}
          loading={removeMutation.isPending}
        />
      )}
    </div>
  )
}
