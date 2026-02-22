import { createRootRouteWithContext, Link, Outlet, useRouter } from '@tanstack/react-router'
import { useMsal, AuthenticatedTemplate, UnauthenticatedTemplate } from '@azure/msal-react'
import { loginRequest } from '../auth/msalConfig'
import type { RouterContext } from '../router'

const IS_MOCK = import.meta.env.VITE_ENABLE_MOCK === 'true'

function NavBar() {
  const { instance, accounts } = useMsal()
  const account = accounts[0]

  function toggleDark() {
    const html = document.documentElement
    html.classList.toggle('dark')
    localStorage.setItem('theme', html.classList.contains('dark') ? 'dark' : 'light')
  }

  function handleSignOut() {
    void instance.logoutRedirect()
  }

  return (
    <nav className="border-b border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link to="/spns" className="font-semibold text-neutral-900 dark:text-neutral-100 text-sm">
            Azure SPN Portal
          </Link>
          <Link
            to="/spns"
            className="text-sm text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors"
            activeProps={{ className: 'text-blue-600 dark:text-blue-400 font-medium' }}
          >
            Service Principals
          </Link>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={toggleDark}
            className="p-1.5 rounded-md text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
            aria-label="Toggle dark mode"
          >
            <svg className="w-4 h-4 dark:hidden" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
            <svg className="w-4 h-4 hidden dark:block" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </button>
          {account && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-neutral-600 dark:text-neutral-400 hidden sm:block">
                {account.username}
              </span>
              <button
                onClick={handleSignOut}
                className="text-sm text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}

function SignInPrompt() {
  const { instance } = useMsal()

  function handleSignIn() {
    void instance.loginRedirect(loginRequest)
  }

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950 flex items-center justify-center">
      <div className="text-center space-y-4">
        <h1 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100">Azure SPN Portal</h1>
        <p className="text-sm text-neutral-600 dark:text-neutral-400">Sign in with your corporate account to continue.</p>
        <button
          onClick={handleSignIn}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          Sign in with Microsoft
        </button>
      </div>
    </div>
  )
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: function RootLayout() {
    if (IS_MOCK) {
      return (
        <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
          <NavBar />
          <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
            <Outlet />
          </main>
        </div>
      )
    }

    return (
      <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
        <AuthenticatedTemplate>
          <NavBar />
          <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
            <Outlet />
          </main>
        </AuthenticatedTemplate>
        <UnauthenticatedTemplate>
          <SignInPrompt />
        </UnauthenticatedTemplate>
      </div>
    )
  },
})
