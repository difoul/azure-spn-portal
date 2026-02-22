import type { Spn, Secret, Owner } from '../api/types'

export const MOCK_SPNS: Spn[] = [
  {
    id: 'spn-001',
    displayName: 'my-ci-pipeline',
    appId: 'aaaaaaaa-0001-0001-0001-aaaaaaaaaaaa',
    description: 'Used by GitLab CI to deploy to dev',
    homepageUrl: null,
    replyUrls: [],
    ownerId: 'user-001',
    ownerUpn: 'alice@company.com',
    secretCount: 1,
    createdAt: '2025-11-10T09:00:00Z',
    portalMetadata: {
      ownerId: 'user-001',
      ownerUpn: 'alice@company.com',
      description: 'Used by GitLab CI to deploy to dev',
      createdAt: '2025-11-10T09:00:00Z',
    },
  },
  {
    id: 'spn-002',
    displayName: 'data-platform-reader',
    appId: 'bbbbbbbb-0002-0002-0002-bbbbbbbbbbbb',
    description: 'Read-only access to storage for the data team',
    homepageUrl: null,
    replyUrls: [],
    ownerId: 'user-001',
    ownerUpn: 'alice@company.com',
    secretCount: 2,
    createdAt: '2025-12-01T14:30:00Z',
    portalMetadata: {
      ownerId: 'user-001',
      ownerUpn: 'alice@company.com',
      description: 'Read-only access to storage for the data team',
      createdAt: '2025-12-01T14:30:00Z',
    },
  },
  {
    id: 'spn-003',
    displayName: 'monitoring-exporter',
    appId: 'cccccccc-0003-0003-0003-cccccccccccc',
    description: null,
    homepageUrl: null,
    replyUrls: [],
    ownerId: 'user-001',
    ownerUpn: 'alice@company.com',
    secretCount: 0,
    createdAt: '2026-01-15T11:00:00Z',
    portalMetadata: {
      ownerId: 'user-001',
      ownerUpn: 'alice@company.com',
      description: null,
      createdAt: '2026-01-15T11:00:00Z',
    },
  },
]

export const MOCK_SECRETS: Record<string, Secret[]> = {
  'spn-001': [
    {
      keyId: 'key-001',
      displayName: 'ci-secret',
      hint: 'aB3',
      startDateTime: '2025-11-10T09:00:00Z',
      endDateTime: '2026-11-10T09:00:00Z',
      keyVaultSecretName: 'spn-my-ci-pipeline-key-001',
    },
  ],
  'spn-002': [
    {
      keyId: 'key-002a',
      displayName: 'primary',
      hint: 'xY9',
      startDateTime: '2025-12-01T14:30:00Z',
      endDateTime: '2026-02-28T14:30:00Z', // expiring soon
      keyVaultSecretName: 'spn-data-platform-reader-key-002a',
    },
    {
      keyId: 'key-002b',
      displayName: 'backup',
      hint: 'mK2',
      startDateTime: '2025-12-01T14:30:00Z',
      endDateTime: '2026-12-01T14:30:00Z',
      keyVaultSecretName: 'spn-data-platform-reader-key-002b',
    },
  ],
  'spn-003': [],
}

export const MOCK_OWNERS: Record<string, Owner[]> = {
  'spn-001': [
    { id: 'user-001', displayName: 'Alice Smith', upn: 'alice@company.com', mail: 'alice@company.com' },
    { id: 'user-002', displayName: 'Bob Jones', upn: 'bob@company.com', mail: 'bob@company.com' },
  ],
  'spn-002': [
    { id: 'user-001', displayName: 'Alice Smith', upn: 'alice@company.com', mail: 'alice@company.com' },
  ],
  'spn-003': [
    { id: 'user-001', displayName: 'Alice Smith', upn: 'alice@company.com', mail: 'alice@company.com' },
  ],
}
