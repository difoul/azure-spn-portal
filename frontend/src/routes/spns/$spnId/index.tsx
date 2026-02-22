import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/spns/$spnId/')({
  beforeLoad: ({ params }) => {
    throw redirect({ to: '/spns/$spnId/secrets', params })
  },
})
