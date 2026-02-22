import { apiFetch } from './client'
import type { Spn, CreateSpnRequest, UpdateSpnRequest } from './types'

export function listSpns(): Promise<Spn[]> {
  return apiFetch<Spn[]>('/spns')
}

export function getSpn(id: string): Promise<Spn> {
  return apiFetch<Spn>(`/spns/${id}`)
}

export function createSpn(req: CreateSpnRequest): Promise<Spn> {
  return apiFetch<Spn>('/spns', {
    method: 'POST',
    body: JSON.stringify(req),
  })
}

export function updateSpn(id: string, req: UpdateSpnRequest): Promise<Spn> {
  return apiFetch<Spn>(`/spns/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(req),
  })
}

export function deleteSpn(id: string): Promise<void> {
  return apiFetch<void>(`/spns/${id}`, { method: 'DELETE' })
}
