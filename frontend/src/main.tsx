import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { MsalProvider } from '@azure/msal-react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { RouterProvider } from '@tanstack/react-router'
import { msalInstance } from './auth/msalConfig'
import { router } from './router'
import './main.css'

const IS_MOCK = import.meta.env.VITE_ENABLE_MOCK === 'true'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

async function prepare() {
  if (IS_MOCK) {
    const { worker } = await import('./mocks/browser')
    return worker.start({ onUnhandledRequest: 'bypass' })
  }
}

prepare().then(() => {
  // In mock mode skip MSAL initialisation — MsalProvider still wraps the tree
  // so useMsal() doesn't throw, but auth guard in __root.tsx is bypassed.
  const boot = IS_MOCK
    ? Promise.resolve()
    : msalInstance.initialize().then(() => msalInstance.handleRedirectPromise())

  return boot
}).then(() => {
  const root = document.getElementById('root')!
  createRoot(root).render(
    <StrictMode>
      <MsalProvider instance={msalInstance}>
        <QueryClientProvider client={queryClient}>
          <RouterProvider router={router} context={{ queryClient }} />
          <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
      </MsalProvider>
    </StrictMode>,
  )
})
