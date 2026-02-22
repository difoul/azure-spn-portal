import { createFileRoute } from '@tanstack/react-router'
import { useMsal } from '@azure/msal-react'
import { OwnerList } from '../../../components/OwnerList'

export const Route = createFileRoute('/spns/$spnId/owners')({
  component: OwnersTab,
})

function OwnersTab() {
  const { spnId } = Route.useParams()
  const { accounts } = useMsal()
  const currentUserOid = accounts[0]?.localAccountId ?? ''
  return <OwnerList spnId={spnId} currentUserOid={currentUserOid} />
}
