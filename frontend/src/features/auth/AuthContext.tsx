import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { ApiRequestError } from '@/services/api'
import {
  fetchMe,
  hasStoredSession,
  login as requestLogin,
  logout as requestLogout,
} from '@/services/auth'
import type { User } from '@/types/api'

type AuthStatus = 'loading' | 'authenticated' | 'anonymous'

interface AuthContextValue {
  user: User | null
  status: AuthStatus
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [status, setStatus] = useState<AuthStatus>('loading')

  // Restore the session from a stored JWT on first load.
  useEffect(() => {
    let cancelled = false

    async function bootstrap() {
      if (!hasStoredSession()) {
        if (!cancelled) setStatus('anonymous')
        return
      }
      try {
        const profile = await fetchMe()
        if (!cancelled) {
          setUser(profile)
          setStatus('authenticated')
        }
      } catch {
        requestLogout()
        if (!cancelled) setStatus('anonymous')
      }
    }

    void bootstrap()
    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    try {
      await requestLogin(email, password)
      const profile = await fetchMe()
      setUser(profile)
      setStatus('authenticated')
    } catch (error) {
      requestLogout()
      setStatus('anonymous')
      throw error
    }
  }, [])

  const logout = useCallback(() => {
    requestLogout()
    setUser(null)
    setStatus('anonymous')
  }, [])

  const value = useMemo(
    () => ({ user, status, login, logout }),
    [user, status, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export { ApiRequestError }
