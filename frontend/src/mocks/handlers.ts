import { http, HttpResponse, delay } from 'msw'
import { MOCK_SPNS, MOCK_SECRETS, MOCK_OWNERS } from './data'
import type { Spn, Secret, Owner, SecretCreated } from '../api/types'

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:7071/api/v1'

// Mutable in-memory state so mutations actually work in the UI
const spns: Spn[] = structuredClone(MOCK_SPNS)
const secrets: Record<string, Secret[]> = structuredClone(MOCK_SECRETS)
const owners: Record<string, Owner[]> = structuredClone(MOCK_OWNERS)

function randomId() {
  return Math.random().toString(36).slice(2, 10)
}

export const handlers = [
  // ----- SPNs -----
  http.get(`${BASE}/spns`, async () => {
    await delay(300)
    return HttpResponse.json(spns)
  }),

  http.get(`${BASE}/spns/:spnId`, async ({ params }) => {
    await delay(200)
    const spn = spns.find(s => s.id === params.spnId)
    if (!spn) return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
    return HttpResponse.json(spn)
  }),

  http.post(`${BASE}/spns`, async ({ request }) => {
    await delay(500)
    const body = await request.json() as { displayName: string; description?: string; homepageUrl?: string; replyUrls?: string[] }
    if (spns.find(s => s.displayName === body.displayName)) {
      return HttpResponse.json({ detail: `SPN with name '${body.displayName}' already exists` }, { status: 409 })
    }
    const newSpn: Spn = {
      id: `spn-${randomId()}`,
      displayName: body.displayName,
      appId: `${randomId()}-${randomId()}-${randomId()}-${randomId()}`,
      description: body.description ?? null,
      homepageUrl: body.homepageUrl ?? null,
      replyUrls: body.replyUrls ?? [],
      ownerId: 'user-001',
      ownerUpn: 'alice@company.com',
      secretCount: 0,
      createdAt: new Date().toISOString(),
      portalMetadata: {
        ownerId: 'user-001',
        ownerUpn: 'alice@company.com',
        description: body.description ?? null,
        createdAt: new Date().toISOString(),
      },
    }
    spns.push(newSpn)
    secrets[newSpn.id] = []
    owners[newSpn.id] = [{ id: 'user-001', displayName: 'Alice Smith', upn: 'alice@company.com', mail: 'alice@company.com' }]
    return HttpResponse.json(newSpn, { status: 201 })
  }),

  http.patch(`${BASE}/spns/:spnId`, async ({ params, request }) => {
    await delay(400)
    const idx = spns.findIndex(s => s.id === params.spnId)
    if (idx === -1) return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
    const body = await request.json() as Partial<Spn>
    spns[idx] = { ...spns[idx], ...body }
    return HttpResponse.json(spns[idx])
  }),

  http.delete(`${BASE}/spns/:spnId`, async ({ params }) => {
    await delay(400)
    const idx = spns.findIndex(s => s.id === params.spnId)
    if (idx === -1) return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
    spns.splice(idx, 1)
    return new HttpResponse(null, { status: 204 })
  }),

  // ----- Secrets -----
  http.get(`${BASE}/spns/:spnId/secrets`, async ({ params }) => {
    await delay(250)
    return HttpResponse.json(secrets[params.spnId as string] ?? [])
  }),

  http.post(`${BASE}/spns/:spnId/secrets`, async ({ params, request }) => {
    await delay(600)
    const spnId = params.spnId as string
    const list = secrets[spnId] ?? []
    if (list.length >= 2) {
      return HttpResponse.json({ detail: 'Maximum of 2 secrets per SPN' }, { status: 422 })
    }
    const body = await request.json() as { displayName: string; expiryMonths?: number }
    const months = body.expiryMonths ?? 12
    const end = new Date()
    end.setMonth(end.getMonth() + months)
    const keyId = `key-${randomId()}`
    const created: SecretCreated = {
      keyId,
      displayName: body.displayName,
      hint: randomId().slice(0, 3),
      startDateTime: new Date().toISOString(),
      endDateTime: end.toISOString(),
      keyVaultSecretName: `spn-${spnId}-${keyId}`,
      secretText: `MOCK_SECRET_${randomId().toUpperCase()}~${randomId().toUpperCase()}`,
    }
    list.push({
      keyId: created.keyId,
      displayName: created.displayName,
      hint: created.hint,
      startDateTime: created.startDateTime,
      endDateTime: created.endDateTime,
      keyVaultSecretName: created.keyVaultSecretName,
    })
    secrets[spnId] = list
    const spn = spns.find(s => s.id === spnId)
    if (spn) spn.secretCount = list.length
    return HttpResponse.json(created, { status: 201 })
  }),

  http.delete(`${BASE}/spns/:spnId/secrets/:keyId`, async ({ params }) => {
    await delay(400)
    const spnId = params.spnId as string
    const list = secrets[spnId] ?? []
    const idx = list.findIndex(s => s.keyId === params.keyId)
    if (idx === -1) return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
    list.splice(idx, 1)
    const spn = spns.find(s => s.id === spnId)
    if (spn) spn.secretCount = list.length
    return new HttpResponse(null, { status: 204 })
  }),

  // ----- Owners -----
  http.get(`${BASE}/spns/:spnId/owners`, async ({ params }) => {
    await delay(250)
    return HttpResponse.json(owners[params.spnId as string] ?? [])
  }),

  http.post(`${BASE}/spns/:spnId/owners`, async ({ params, request }) => {
    await delay(500)
    const spnId = params.spnId as string
    const body = await request.json() as { upn: string }
    const list = owners[spnId] ?? []
    if (list.find(o => o.upn === body.upn)) {
      return HttpResponse.json({ detail: 'User is already an owner' }, { status: 409 })
    }
    const newOwner: Owner = {
      id: `user-${randomId()}`,
      displayName: body.upn.split('@')[0] ?? body.upn,
      upn: body.upn,
      mail: body.upn,
    }
    list.push(newOwner)
    owners[spnId] = list
    return HttpResponse.json(newOwner, { status: 201 })
  }),

  http.delete(`${BASE}/spns/:spnId/owners/:ownerId`, async ({ params }) => {
    await delay(400)
    const spnId = params.spnId as string
    const list = owners[spnId] ?? []
    const idx = list.findIndex(o => o.id === params.ownerId)
    if (idx === -1) return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
    list.splice(idx, 1)
    return new HttpResponse(null, { status: 204 })
  }),
]
