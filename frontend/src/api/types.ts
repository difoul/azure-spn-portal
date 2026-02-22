// TypeScript types mirroring backend Pydantic models

export interface Spn {
  id: string
  displayName: string
  appId: string
  description: string | null
  homepageUrl: string | null
  replyUrls: string[]
  ownerId: string
  ownerUpn: string
  secretCount: number
  createdAt: string
  portalMetadata: {
    ownerId: string
    ownerUpn: string
    description: string | null
    createdAt: string
  }
}

export interface CreateSpnRequest {
  displayName: string
  description?: string
  homepageUrl?: string
  replyUrls?: string[]
}

export interface UpdateSpnRequest {
  description?: string
  homepageUrl?: string
  replyUrls?: string[]
}

export interface Secret {
  keyId: string
  displayName: string
  hint: string
  startDateTime: string
  endDateTime: string
  keyVaultSecretName: string
}

export interface CreateSecretRequest {
  displayName: string
  expiryMonths?: number
}

export interface SecretCreated {
  keyId: string
  displayName: string
  hint: string
  startDateTime: string
  endDateTime: string
  keyVaultSecretName: string
  secretText: string
}

export interface Owner {
  id: string
  displayName: string
  upn: string
  mail: string | null
}

export interface AddOwnerRequest {
  upn: string
}

export interface ApiError {
  detail: string
  status: number
}
