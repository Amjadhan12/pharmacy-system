/** Centralised route paths — keep in sync with routes/index.tsx. */
export const paths = {
  dashboard: '/',
  login: '/login',
  pos: '/pos',
  medicines: '/medicines',
  inventory: '/inventory',
  purchasing: '/purchasing',
  suppliers: '/suppliers',
  customers: '/customers',
  prescriptions: '/prescriptions',
  accounting: '/accounting',
  expenses: '/expenses',
  cashBank: '/cash-bank',
  reports: '/reports',
  aiCfo: '/ai-cfo',
  chat: '/chat',
  branches: '/branches',
  staff: '/staff',
  settings: '/settings',
} as const

export type PathKey = keyof typeof paths
