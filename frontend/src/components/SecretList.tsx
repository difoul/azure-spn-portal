import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useQuery } from '@tanstack/react-query'
import { Badge } from './ui/Badge'
import { Button } from './ui/Button'
import { ConfirmDialog } from './ConfirmDialog'
import { SecretRevealModal } from './SecretRevealModal'
import { Input } from './ui/Input'
import { Spinner } from './ui/Spinner'
import { formatDate, isExpired, isExpiringSoon } from '../lib/utils'
import { listSecrets, createSecret, deleteSecret } from '../api/secrets'
import type { SecretCreated } from '../api/types'

interface SecretListProps {
  spnId: string
}

export function SecretList({ spnId }: SecretListProps) {
  const queryClient = useQueryClient()
  const [deletingKeyId, setDeletingKeyId] = useState<string | null>(null)
  const [revealedSecret, setRevealedSecret] = useState<SecretCreated | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newSecretName, setNewSecretName] = useState('')
  const [expiryMonths, setExpiryMonths] = useState('12')

  const { data: secrets, isLoading, error } = useQuery({
    queryKey: ['spns', spnId, 'secrets'],
    queryFn: () => listSecrets(spnId),
  })

  const createMutation = useMutation({
    mutationFn: () => createSecret(spnId, { displayName: newSecretName.trim(), expiryMonths: parseInt(expiryMonths, 10) }),
    onSuccess: (created) => {
      void queryClient.invalidateQueries({ queryKey: ['spns', spnId, 'secrets'] })
      void queryClient.invalidateQueries({ queryKey: ['spns'] })
      setRevealedSecret(created)
      setShowAddForm(false)
      setNewSecretName('')
      setExpiryMonths('12')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (keyId: string) => deleteSecret(spnId, keyId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['spns', spnId, 'secrets'] })
      void queryClient.invalidateQueries({ queryKey: ['spns'] })
      setDeletingKeyId(null)
    },
  })

  if (isLoading) return <div className="flex justify-center py-8"><Spinner /></div>
  if (error) return <p className="text-red-500 text-sm">Failed to load secrets.</p>

  const canAdd = (secrets?.length ?? 0) < 2

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300">
          Client Secrets ({secrets?.length ?? 0} / 2)
        </h3>
        {canAdd && !showAddForm && (
          <Button size="sm" onClick={() => setShowAddForm(true)}>
            Add secret
          </Button>
        )}
      </div>

      {showAddForm && (
        <form
          className="rounded-lg border border-neutral-200 dark:border-neutral-700 p-4 space-y-3"
          onSubmit={e => { e.preventDefault(); createMutation.mutate() }}
        >
          <Input
            label="Display name"
            value={newSecretName}
            onChange={e => setNewSecretName(e.target.value)}
            placeholder="ci-pipeline-secret"
            required
            autoFocus
          />
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300">Expires in (months)</label>
            <select
              value={expiryMonths}
              onChange={e => setExpiryMonths(e.target.value)}
              className="block w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm
                dark:border-neutral-600 dark:bg-neutral-900 dark:text-neutral-100
                focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="6">6 months</option>
              <option value="12">12 months</option>
              <option value="24">24 months</option>
            </select>
          </div>
          {createMutation.error && (
            <p className="text-sm text-red-500">{(createMutation.error as Error).message}</p>
          )}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" size="sm" onClick={() => setShowAddForm(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" loading={createMutation.isPending} disabled={!newSecretName.trim()}>
              Create
            </Button>
          </div>
        </form>
      )}

      {secrets && secrets.length === 0 && !showAddForm && (
        <p className="text-sm text-neutral-500 dark:text-neutral-400 py-4 text-center">No secrets yet.</p>
      )}

      {secrets && secrets.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-neutral-200 dark:border-neutral-700">
          <table className="min-w-full divide-y divide-neutral-200 dark:divide-neutral-700">
            <thead className="bg-neutral-50 dark:bg-neutral-800">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">Hint</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">Expires</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">Key Vault</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-200 dark:divide-neutral-700 bg-white dark:bg-neutral-900">
              {secrets.map(secret => {
                const expired = isExpired(secret.endDateTime)
                const expiring = isExpiringSoon(secret.endDateTime)
                return (
                  <tr key={secret.keyId} className="hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors">
                    <td className="px-4 py-3 text-sm text-neutral-900 dark:text-neutral-100">{secret.displayName}</td>
                    <td className="px-4 py-3 text-sm font-mono text-neutral-600 dark:text-neutral-400">{secret.hint}...</td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex items-center gap-2">
                        <span className="text-neutral-600 dark:text-neutral-400">{formatDate(secret.endDateTime)}</span>
                        {expired && <Badge variant="red">Expired</Badge>}
                        {!expired && expiring && <Badge variant="yellow">Expiring soon</Badge>}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-neutral-500 dark:text-neutral-400">{secret.keyVaultSecretName}</td>
                    <td className="px-4 py-3 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
                        onClick={() => setDeletingKeyId(secret.keyId)}
                      >
                        Delete
                      </Button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {deletingKeyId && (
        <ConfirmDialog
          title="Delete Secret"
          message="Are you sure you want to delete this secret? Any applications using it will stop working."
          onConfirm={() => deleteMutation.mutate(deletingKeyId)}
          onCancel={() => setDeletingKeyId(null)}
          loading={deleteMutation.isPending}
        />
      )}

      {revealedSecret && (
        <SecretRevealModal
          secret={revealedSecret}
          onClose={() => setRevealedSecret(null)}
        />
      )}
    </div>
  )
}
