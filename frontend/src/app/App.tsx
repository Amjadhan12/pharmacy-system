import { AppProviders } from '@/app/providers'
import { AppRouter } from '@/routes'

export default function App() {
  return (
    <AppProviders>
      <AppRouter />
    </AppProviders>
  )
}
