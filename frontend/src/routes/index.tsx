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
const modules = [
  { path: paths.pos, title: 'Point of Sale' },
  {
    path: paths.medicines,
    title: 'Medicines',
    apiPath: '/medicines/medicines/',
    columns: [
      { key: 'generic_name', label: 'Generic name' },
      { key: 'brand_name', label: 'Brand name' },
      { key: 'strength', label: 'Strength' },
      { key: 'category', label: 'Category ID' },
      { key: 'dosage_form', label: 'Dosage form ID' },
      { key: 'is_active', label: 'Active' },
    ],
  },
  {
    path: paths.inventory,
    title: 'Inventory',
    apiPath: '/medicines/batches/',
    columns: [
      { key: 'batch_number', label: 'Batch' },
      { key: 'medicine', label: 'Medicine ID' },
      { key: 'branch', label: 'Branch ID' },
      { key: 'warehouse', label: 'Warehouse ID' },
      { key: 'quantity', label: 'Quantity' },
      { key: 'expiry_date', label: 'Expiry date' },
      { key: 'status', label: 'Status' },
    ],
  },
  { path: paths.purchasing, title: 'Purchasing' },
  {
    path: paths.suppliers,
    title: 'Suppliers',
    apiPath: '/suppliers/',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'email', label: 'Email' },
      { key: 'phone', label: 'Phone' },
      { key: 'city', label: 'City' },
      { key: 'currency', label: 'Currency' },
    ],
  },
  {
    path: paths.customers,
    title: 'Customers',
    apiPath: '/customers/',
    columns: [
      { key: 'first_name', label: 'First name' },
      { key: 'last_name', label: 'Last name' },
      { key: 'email', label: 'Email' },
      { key: 'phone', label: 'Phone' },
      { key: 'city', label: 'City' },
    ],
  },
  { path: paths.prescriptions, title: 'Prescriptions' },
  {
    path: paths.accounting,
    title: 'Accounting',
    apiPath: '/accounting/accounts/',
    columns: [
      { key: 'account_code', label: 'Account code' },
      { key: 'name', label: 'Name' },
      { key: 'account_type', label: 'Type' },
      { key: 'currency', label: 'Currency' },
      { key: 'pharmacy', label: 'Pharmacy ID' },
    ],
  },
  { path: paths.expenses, title: 'Expenses' },
  { path: paths.cashBank, title: 'Cash & Bank' },
  { path: paths.reports, title: 'Reports' },
  { path: paths.aiCfo, title: 'AI CFO' },
  { path: paths.chat, title: 'Chat' },
  {
    path: paths.branches,
    title: 'Branches',
    apiPath: '/branches/',
    columns: [
      { key: 'name', label: 'Branch' },
      { key: 'code', label: 'Code' },
      { key: 'city', label: 'City' },
      { key: 'pharmacy', label: 'Pharmacy ID' },
      { key: 'status', label: 'Status' },
    ],
  },
  { path: paths.staff, title: 'Staff' },
  {
    path: paths.settings,
    title: 'Pharmacies',
    apiPath: '/pharmacies/',
    columns: [
      { key: 'name', label: 'Pharmacy' },
      { key: 'city', label: 'City' },
      { key: 'country', label: 'Country' },
      { key: 'currency', label: 'Currency' },
      { key: 'status', label: 'Status' },
    ],
  },
]

const router = createBrowserRouter([
  { path: paths.login, element: <LoginPage /> },
  {
    element: <AppShell />,
    children: [
      { path: paths.dashboard, element: <DashboardPage /> },
      ...modules.map((module) => ({
        path: module.path,
        element: (
          <ModulePage
            title={module.title}
            apiPath={'apiPath' in module ? module.apiPath : undefined}
            columns={'columns' in module ? module.columns : undefined}
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
