import { apiFetch } from './client'
import type { Secret, CreateSecretRequest, SecretCreated } from './types'

export function listSecrets(spnId: string): Promise<Secret[]> {
  return apiFetch<Secret[]>(`/spns/${spnId}/secrets`)
}

export function createSecret(spnId: string, req: CreateSecretRequest): Promise<SecretCreated> {
  return apiFetch<SecretCreated>(`/spns/${spnId}/secrets`, {
    method: 'POST',
    body: JSON.stringify(req),
  })
}

export function deleteSecret(spnId: string, keyId: string): Promise<void> {
  return apiFetch<void>(`/spns/${spnId}/secrets/${keyId}`, { method: 'DELETE' })
}
