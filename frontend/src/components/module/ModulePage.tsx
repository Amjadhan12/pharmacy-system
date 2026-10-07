import { Construction } from 'lucide-react'
import EmptyState from '@/components/ui/EmptyState'

interface ModulePageProps {
  title: string
  apiSegment: string
}

/**
 * Honest placeholder for modules that are not implemented yet.
 * It renders no fabricated data — only a status message.
 */
export default function ModulePage({ title, apiSegment }: ModulePageProps) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Module scheduled for an upcoming sprint.
        </p>
      </div>
      <EmptyState
        icon={<Construction className="h-6 w-6" />}
        title={`${title} is being built`}
        description={`This screen will load live data from /api/v1/${apiSegment}/ once the module lands. No sample data is shown in the meantime.`}
      />
    </div>
  )
}
