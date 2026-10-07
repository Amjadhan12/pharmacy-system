import { zodResolver } from '@hookform/resolvers/zod'
import { useState, type FormEvent } from 'react'
import { useForm } from 'react-hook-form'
import { Navigate, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import Input from '@/components/ui/Input'
import { ApiRequestError, useAuth } from '@/features/auth/AuthContext'
import { paths } from '@/routes/paths'

const loginSchema = z.object({
  email: z.email('Enter a valid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

type LoginFormValues = z.infer<typeof loginSchema>

export default function LoginPage() {
  const { user, status, login } = useAuth()
  const navigate = useNavigate()
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  if (status === 'authenticated' && user) {
    return <Navigate to={paths.dashboard} replace />
  }

  async function onSubmit(values: LoginFormValues) {
    setServerError(null)
    try {
      await login(values.email, values.password)
      navigate(paths.dashboard, { replace: true })
    } catch (error) {
      setServerError(
        error instanceof ApiRequestError
          ? error.message
          : 'Unable to sign in right now. Please try again.',
      )
    }
  }

  // Prevent an empty form submit from bypassing RHF while JS resolves.
  function onInvalidHandler(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
  }

  return (
    <div className="flex min-h-full items-center justify-center bg-zinc-50 px-4 py-12 dark:bg-zinc-950">
      <div className="w-full max-w-md space-y-6">
        <div className="flex items-center justify-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-600 text-base font-bold text-white">
            PF
          </div>
          <div>
            <h1 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">
              PharmaFin
            </h1>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Pharmacy Financial &amp; Management System
            </p>
          </div>
        </div>

        <Card className="p-6 sm:p-8">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            Sign in
          </h2>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Use your work email and password.
          </p>

          {serverError && (
            <div
              role="alert"
              className="mt-4 rounded-lg bg-rose-50 px-3.5 py-2.5 text-sm text-rose-700 ring-1 ring-inset ring-rose-200 dark:bg-rose-950 dark:text-rose-300 dark:ring-rose-900"
            >
              {serverError}
            </div>
          )}

          <form
            className="mt-5 space-y-4"
            onSubmit={handleSubmit(onSubmit)}
            onInvalid={onInvalidHandler}
            noValidate
          >
            <Input
              label="Email address"
              type="email"
              autoComplete="email"
              placeholder="you@pharmacy.com"
              error={errors.email?.message}
              {...register('email')}
            />
            <Input
              label="Password"
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              error={errors.password?.message}
              {...register('password')}
            />
            <Button
              type="submit"
              className="w-full"
              loading={isSubmitting}
            >
              Sign in
            </Button>
          </form>
        </Card>

        <p className="text-center text-xs text-zinc-400 dark:text-zinc-500">
          Google sign-in will be enabled in the authentication sprint.
        </p>
      </div>
    </div>
  )
}
