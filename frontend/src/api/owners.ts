import { apiFetch } from './client'
import type { Owner, AddOwnerRequest } from './types'

export function listOwners(spnId: string): Promise<Owner[]> {
  return apiFetch<Owner[]>(`/spns/${spnId}/owners`)
}

export function addOwner(spnId: string, req: AddOwnerRequest): Promise<Owner> {
  return apiFetch<Owner>(`/spns/${spnId}/owners`, {
    method: 'POST',
    body: JSON.stringify(req),
  })
}

export function removeOwner(spnId: string, ownerId: string): Promise<void> {
  return apiFetch<void>(`/spns/${spnId}/owners/${ownerId}`, { method: 'DELETE' })
}
