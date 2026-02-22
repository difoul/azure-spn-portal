import { useState } from 'react'
import { Button } from './ui/Button'
import type { SecretCreated } from '../api/types'

interface SecretRevealModalProps {
  secret: SecretCreated
  onClose: () => void
}

export function SecretRevealModal({ secret, onClose }: SecretRevealModalProps) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(secret.secretText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" />
      <div className="relative z-10 w-full max-w-lg rounded-lg bg-white dark:bg-neutral-900 p-6 shadow-xl">
        <div className="flex items-start gap-3 mb-4">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-yellow-100 dark:bg-yellow-900/40 flex items-center justify-center">
            <svg className="w-4 h-4 text-yellow-600 dark:text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            </svg>
          </div>
          <div>
            <h2 className="text-base font-semibold text-neutral-900 dark:text-neutral-100">
              Secret created — copy it now
            </h2>
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-0.5">
              This value will never be shown again. It is also stored in Key Vault as{' '}
              <code className="text-xs bg-neutral-100 dark:bg-neutral-800 px-1 py-0.5 rounded">
                {secret.keyVaultSecretName}
              </code>
              .
            </p>
          </div>
        </div>

        <div className="mb-4">
          <p className="text-xs font-medium text-neutral-500 dark:text-neutral-400 mb-1">Secret value</p>
          <div className="relative">
            <pre className="overflow-x-auto rounded-md bg-neutral-100 dark:bg-neutral-800 p-3 text-sm font-mono text-neutral-900 dark:text-neutral-100 break-all whitespace-pre-wrap">
              {secret.secretText}
            </pre>
          </div>
        </div>

        <div className="mb-4 grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">Display name</p>
            <p className="text-neutral-900 dark:text-neutral-100">{secret.displayName}</p>
          </div>
          <div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">Hint</p>
            <p className="text-neutral-900 dark:text-neutral-100 font-mono">{secret.hint}...</p>
          </div>
          <div>
            <p className="text-xs text-neutral-500 dark:text-neutral-400">Expires</p>
            <p className="text-neutral-900 dark:text-neutral-100">
              {new Date(secret.endDateTime).toLocaleDateString('en-GB', { year: 'numeric', month: 'short', day: 'numeric' })}
            </p>
          </div>
        </div>

        <div className="flex justify-between gap-3">
          <Button variant="secondary" size="sm" onClick={handleCopy}>
            {copied ? '✓ Copied!' : 'Copy to clipboard'}
          </Button>
          <Button onClick={onClose}>
            I've copied the secret
          </Button>
        </div>
      </div>
    </div>
  )
}
