import { createFileRoute } from '@tanstack/react-router'
import { SecretList } from '../../../components/SecretList'

export const Route = createFileRoute('/spns/$spnId/secrets')({
  component: SecretsTab,
})

function SecretsTab() {
  const { spnId } = Route.useParams()
  return <SecretList spnId={spnId} />
}
