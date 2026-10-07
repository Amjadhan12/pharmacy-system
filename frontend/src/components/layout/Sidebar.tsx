import {
  Boxes,
  BrainCircuit,
  Building2,
  ChartNoAxesCombined,
  FileText,
  Landmark,
  LayoutDashboard,
  MessageSquare,
  PackagePlus,
  Pill,
  Receipt,
  ScanBarcode,
  Settings,
  Truck,
  UserCog,
  Users,
  Wallet,
  type LucideIcon,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { paths } from '@/routes/paths'

interface NavItem {
  to: string
  label: string
  icon: LucideIcon
}

interface NavSection {
  label: string
  items: NavItem[]
}

const sections: NavSection[] = [
  {
    label: 'Overview',
    items: [{ to: paths.dashboard, label: 'Dashboard', icon: LayoutDashboard }],
  },
  {
    label: 'Sales',
    items: [{ to: paths.pos, label: 'POS', icon: ScanBarcode }],
  },
  {
    label: 'Catalog',
    items: [
      { to: paths.medicines, label: 'Medicines', icon: Pill },
      { to: paths.inventory, label: 'Inventory', icon: Boxes },
    ],
  },
  {
    label: 'Supply chain',
    items: [
      { to: paths.purchasing, label: 'Purchasing', icon: PackagePlus },
      { to: paths.suppliers, label: 'Suppliers', icon: Truck },
    ],
  },
  {
    label: 'Relations',
    items: [
      { to: paths.customers, label: 'Customers', icon: Users },
      { to: paths.prescriptions, label: 'Prescriptions', icon: FileText },
    ],
  },
  {
    label: 'Finance',
    items: [
      { to: paths.accounting, label: 'Accounting', icon: Landmark },
      { to: paths.expenses, label: 'Expenses', icon: Receipt },
      { to: paths.cashBank, label: 'Cash & Bank', icon: Wallet },
      { to: paths.reports, label: 'Reports', icon: ChartNoAxesCombined },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { to: paths.aiCfo, label: 'AI CFO', icon: BrainCircuit },
      { to: paths.chat, label: 'Chat', icon: MessageSquare },
    ],
  },
  {
    label: 'Administration',
    items: [
      { to: paths.branches, label: 'Branches', icon: Building2 },
      { to: paths.staff, label: 'Staff', icon: UserCog },
      { to: paths.settings, label: 'Settings', icon: Settings },
    ],
  },
]

interface SidebarProps {
  onNavigate?: () => void
  className?: string
}

export default function Sidebar({ onNavigate, className }: SidebarProps) {
  return (
    <aside
      className={cn(
        'flex h-full w-64 flex-col border-r border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950',
        className,
      )}
    >
      <div className="flex h-16 items-center gap-2.5 border-b border-zinc-100 px-5 dark:border-zinc-800">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600 text-sm font-bold text-white">
          PF
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            PharmaFin
          </p>
          <p className="text-[11px] text-zinc-500 dark:text-zinc-400">
            Pharmacy OS
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
        {sections.map((section) => (
          <div key={section.label}>
            <p className="px-2 text-[11px] font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-500">
              {section.label}
            </p>
            <ul className="mt-1.5 space-y-0.5">
              {section.items.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.to === paths.dashboard}
                    onClick={onNavigate}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                          : 'text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-900 dark:hover:text-zinc-100',
                      )
                    }
                  >
                    <item.icon className="h-4 w-4 shrink-0" aria-hidden />
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-zinc-100 px-5 py-3 dark:border-zinc-800">
        <p className="text-[11px] text-zinc-400 dark:text-zinc-500">
          v0.1.0 · Foundation
        </p>
      </div>
    </aside>
  )
}
