import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { SpnForm } from '../../components/SpnForm'
import { createSpn } from '../../api/spns'
import { ApiRequestError } from '../../api/client'
import type { CreateSpnRequest } from '../../api/types'

export const Route = createFileRoute('/spns/new')({
  component: NewSpnPage,
})

function NewSpnPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: (req: CreateSpnRequest) => createSpn(req),
    onSuccess: (spn) => {
      void queryClient.invalidateQueries({ queryKey: ['spns'] })
      void navigate({ to: '/spns/$spnId/secrets', params: { spnId: spn.id } })
    },
  })

  function handleCancel() {
    void navigate({ to: '/spns' })
  }

  const errorMessage = mutation.error instanceof ApiRequestError
    ? mutation.error.detail
    : mutation.error instanceof Error
    ? mutation.error.message
    : null

  return (
    <div className="max-w-lg">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">Create Service Principal</h1>
        <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-0.5">
          You will become the owner of the new SPN.
        </p>
      </div>
      <SpnForm
        onSubmit={mutation.mutate}
        onCancel={handleCancel}
        loading={mutation.isPending}
        error={errorMessage}
      />
    </div>
  )
}
