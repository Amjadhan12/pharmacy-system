import { RouterProvider, createBrowserRouter } from 'react-router-dom'
import AppShell from '@/components/layout/AppShell'
import DataModulePage, { type DataModuleField } from '@/components/module/DataModulePage'
import ModulePage from '@/components/module/ModulePage'
import LoginPage from '@/features/auth/LoginPage'
import DashboardPage from '@/features/dashboard/DashboardPage'
import InventoryPage from '@/features/inventory/InventoryPage'
import MedicineDetailPage from '@/features/medicines/MedicineDetailPage'
import { paths } from './paths'

/**
 * Modules that are scheduled but not implemented yet render an honest
 * placeholder (no fake data). When a module is built, its feature folder
 * replaces the corresponding entry here.
 */
interface ModuleRoute {
  path: string
  title: string
  apiPath?: string
  columns?: { key: string; label: string }[]
  fields?: DataModuleField[]
  canWriteRoles?: string[]
  filters?: {
    key: string
    label: string
    choices?: { value: string; label: string }[]
    lookup?: string
  }[]
  rowDetailPath?: string
}

const modules: ModuleRoute[] = [
  { path: paths.pos, title: 'Point of Sale' },
  {
    path: paths.medicines,
    title: 'Medicines',
    apiPath: '/medicines/medicines/',
    rowDetailPath: '/medicines/',
    canWriteRoles: ['pharmacy_owner', 'pharmacy_manager', 'pharmacist', 'inventory_manager'],
    filters: [
      { key: 'category', label: 'Category', lookup: '/medicines/categories/' },
      { key: 'manufacturer', label: 'Manufacturer', lookup: '/medicines/manufacturers/' },
      {
        key: 'is_active',
        label: 'Status',
        choices: [
          { value: 'true', label: 'Active' },
          { value: 'false', label: 'Inactive' },
        ],
      },
    ],
    fields: [
      { key: 'generic_name', label: 'Generic name', required: true },
      { key: 'brand_name', label: 'Brand name' },
      { key: 'manufacturer', label: 'Manufacturer', type: 'select', lookup: '/medicines/manufacturers/' },
      { key: 'category', label: 'Category', type: 'select', lookup: '/medicines/categories/', required: true },
      { key: 'dosage_form', label: 'Dosage form', type: 'select', lookup: '/medicines/dosage-forms/', required: true },
      { key: 'strength', label: 'Strength' },
      { key: 'route', label: 'Route', type: 'select', choices: [
        { value: 'oral', label: 'Oral' }, { value: 'topical', label: 'Topical' },
        { value: 'intravenous', label: 'Intravenous' }, { value: 'intramuscular', label: 'Intramuscular' },
        { value: 'ophthalmic', label: 'Ophthalmic' }, { value: 'nasal', label: 'Nasal' },
      ] },
      { key: 'barcode', label: 'Barcode' },
      { key: 'gtin', label: 'GTIN' },
      { key: 'description', label: 'Description', type: 'textarea' },
      { key: 'prescription_required', label: 'Prescription required', type: 'checkbox' },
      { key: 'reorder_level', label: 'Low-stock threshold', type: 'number' },
      { key: 'storage_condition', label: 'Storage condition', type: 'select', choices: [
        { value: 'room_temperature', label: 'Room temperature' }, { value: 'cool', label: 'Cool' },
        { value: 'cold', label: 'Cold' }, { value: 'dry', label: 'Dry' },
        { value: 'frozen', label: 'Frozen' }, { value: 'protect_from_light', label: 'Protect from light' },
      ] },
      { key: 'is_active', label: 'Active', type: 'checkbox' },
    ],
    columns: [
      { key: 'generic_name', label: 'Generic name' },
      { key: 'brand_name', label: 'Brand name' },
      { key: 'manufacturer_name', label: 'Manufacturer' },
      { key: 'strength', label: 'Strength' },
      { key: 'category_name', label: 'Category' },
      { key: 'dosage_form_name', label: 'Dosage form' },
      { key: 'reorder_level', label: 'Low-stock threshold' },
      { key: 'is_active', label: 'Active' },
    ],
  },
  { path: paths.purchasing, title: 'Purchasing' },
  {
    path: paths.suppliers,
    title: 'Suppliers',
    apiPath: '/suppliers/',
    canWriteRoles: ['pharmacy_owner', 'pharmacy_manager', 'inventory_manager'],
    fields: [
      { key: 'name', label: 'Name', required: true },
      { key: 'legal_name', label: 'Legal name' },
      { key: 'email', label: 'Email', type: 'email' },
      { key: 'phone', label: 'Phone' },
      { key: 'tax_number', label: 'Tax number' },
      { key: 'address', label: 'Address', type: 'textarea' },
      { key: 'city', label: 'City' },
      { key: 'country', label: 'Country code' },
      { key: 'payment_terms_days', label: 'Payment terms (days)', type: 'number' },
      { key: 'currency', label: 'Currency' },
      { key: 'is_active', label: 'Active', type: 'checkbox' },
    ],
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
    canWriteRoles: ['pharmacy_owner', 'pharmacy_manager', 'pharmacist', 'cashier'],
    fields: [
      { key: 'first_name', label: 'First name', required: true },
      { key: 'last_name', label: 'Last name' },
      { key: 'email', label: 'Email', type: 'email', required: true },
      { key: 'phone', label: 'Phone' },
      { key: 'address', label: 'Address', type: 'textarea' },
      { key: 'city', label: 'City' },
      { key: 'country', label: 'Country code' },
      { key: 'notes', label: 'Notes', type: 'textarea' },
      { key: 'is_active', label: 'Active', type: 'checkbox' },
    ],
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
      { path: paths.inventory, element: <InventoryPage /> },
      { path: paths.medicineDetail, element: <MedicineDetailPage /> },
      ...modules.map((module) => ({
        path: module.path,
        element: (
          module.fields && module.apiPath && module.columns ? (
            <DataModulePage
              title={module.title}
              apiPath={module.apiPath}
              columns={module.columns}
              fields={module.fields}
              canWriteRoles={module.canWriteRoles}
              filters={module.filters}
              rowDetailPath={module.rowDetailPath}
            />
          ) : (
            <ModulePage
              title={module.title}
              apiPath={'apiPath' in module ? module.apiPath : undefined}
              columns={'columns' in module ? module.columns : undefined}
            />
          )
        ),
      })),
      { path: '*', element: <DashboardPage /> },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
