import { useState } from 'react'
import { Input } from './ui/Input'
import { Button } from './ui/Button'
import type { CreateSpnRequest } from '../api/types'

interface SpnFormProps {
  onSubmit: (req: CreateSpnRequest) => void
  onCancel: () => void
  loading?: boolean
  error?: string | null
}

export function SpnForm({ onSubmit, onCancel, loading, error }: SpnFormProps) {
  const [displayName, setDisplayName] = useState('')
  const [description, setDescription] = useState('')
  const [homepageUrl, setHomepageUrl] = useState('')
  const [replyUrls, setReplyUrls] = useState('')

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const req: CreateSpnRequest = {
      displayName: displayName.trim(),
      ...(description.trim() && { description: description.trim() }),
      ...(homepageUrl.trim() && { homepageUrl: homepageUrl.trim() }),
      ...(replyUrls.trim() && {
        replyUrls: replyUrls.split('\n').map(u => u.trim()).filter(Boolean),
      }),
    }
    onSubmit(req)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        label="Display Name"
        value={displayName}
        onChange={e => setDisplayName(e.target.value)}
        placeholder="my-service-principal"
        required
        autoFocus
      />
      <Input
        label="Description"
        value={description}
        onChange={e => setDescription(e.target.value)}
        placeholder="Optional description"
      />
      <Input
        label="Homepage URL"
        type="url"
        value={homepageUrl}
        onChange={e => setHomepageUrl(e.target.value)}
        placeholder="https://example.com"
      />
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
          Reply URLs <span className="text-neutral-400 font-normal">(one per line)</span>
        </label>
        <textarea
          value={replyUrls}
          onChange={e => setReplyUrls(e.target.value)}
          placeholder="https://example.com/callback"
          rows={3}
          className="block w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm shadow-sm
            dark:border-neutral-600 dark:bg-neutral-900 dark:text-neutral-100
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {error && (
        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
      )}

      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={loading}>
          Cancel
        </Button>
        <Button type="submit" loading={loading} disabled={!displayName.trim()}>
          Create SPN
        </Button>
      </div>
    </form>
  )
}
