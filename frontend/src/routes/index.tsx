import { RouterProvider, createBrowserRouter } from 'react-router-dom'
import AppShell from '@/components/layout/AppShell'
import ModulePage from '@/components/module/ModulePage'
import LoginPage from '@/features/auth/LoginPage'
import DashboardPage from '@/features/dashboard/DashboardPage'
import { paths } from './paths'

/**
 * Modules that are scheduled but not implemented yet render an honest
 * placeholder (no fake data). When a module is built, its feature folder
 * replaces the corresponding entry here.
 */
const pendingModules = [
  { path: paths.pos, title: 'Point of Sale', segment: 'sales' },
  { path: paths.medicines, title: 'Medicines', segment: 'medicines' },
  { path: paths.inventory, title: 'Inventory', segment: 'inventory' },
  { path: paths.purchasing, title: 'Purchasing', segment: 'purchases' },
  { path: paths.suppliers, title: 'Suppliers', segment: 'suppliers' },
  { path: paths.customers, title: 'Customers', segment: 'customers' },
  { path: paths.prescriptions, title: 'Prescriptions', segment: 'prescriptions' },
  { path: paths.accounting, title: 'Accounting', segment: 'accounting' },
  { path: paths.expenses, title: 'Expenses', segment: 'expenses' },
  { path: paths.cashBank, title: 'Cash & Bank', segment: 'payments' },
  { path: paths.reports, title: 'Reports', segment: 'reports' },
  { path: paths.aiCfo, title: 'AI CFO', segment: 'ai' },
  { path: paths.chat, title: 'Chat', segment: 'chat' },
  { path: paths.branches, title: 'Branches', segment: 'branches' },
  { path: paths.staff, title: 'Staff', segment: 'accounts' },
  { path: paths.settings, title: 'Settings', segment: 'pharmacies' },
]

const router = createBrowserRouter([
  { path: paths.login, element: <LoginPage /> },
  {
    element: <AppShell />,
    children: [
      { path: paths.dashboard, element: <DashboardPage /> },
      ...pendingModules.map((module) => ({
        path: module.path,
        element: (
          <ModulePage
            title={module.title}
            apiSegment={module.segment}
          />
        ),
      })),
      { path: '*', element: <DashboardPage /> },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
