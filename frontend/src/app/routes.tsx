/**
 * Route configuration — role-based routing with guards.
 * Each dashboard section is wrapped in a RequireRole guard.
 */
import { createBrowserRouter, Navigate } from 'react-router-dom';
import AppShell from '../components/layout/AppShell';
import RequireRole from './guards/RequireRole';
import LoginPage from '../features/auth/LoginPage';

// Dashboard pages (lazy-loadable in future, direct imports for Phase 1)
import CitizenDashboardPage from '../features/citizen/pages/DashboardPage';
import OfficerDashboardPage from '../features/officer/pages/DashboardPage';
import ControllerDashboardPage from '../features/controller/pages/DashboardPage';
import NationalAdminDashboardPage from '../features/national-admin/pages/DashboardPage';
import BusinessDashboardPage from '../features/business-portal/pages/DashboardPage';
import EcommerceDashboardPage from '../features/ecommerce-integration/pages/DashboardPage';
import RuleAdminDashboardPage from '../features/rule-admin/pages/DashboardPage';

export const router = createBrowserRouter([
  // Public routes
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <LoginPage />,
  },

  // Protected routes within the AppShell
  {
    element: <AppShell />,
    children: [
      // === Citizen ===
      {
        element: <RequireRole allowedRoles={['citizen']} />,
        children: [
          { path: '/citizen', element: <CitizenDashboardPage /> },
          // Phase 4: more citizen screens will be added here
        ],
      },

      // === Field Officer ===
      {
        element: <RequireRole allowedRoles={['field_officer']} />,
        children: [
          { path: '/officer', element: <OfficerDashboardPage /> },
          // Phase 4: queue, capture, cases screens
        ],
      },

      // === State Controller ===
      {
        element: <RequireRole allowedRoles={['state_controller']} />,
        children: [
          { path: '/controller', element: <ControllerDashboardPage /> },
          // Phase 4: heatmap, assignments, escalations
        ],
      },

      // === National Admin ===
      {
        element: <RequireRole allowedRoles={['national_admin']} />,
        children: [
          { path: '/national', element: <NationalAdminDashboardPage /> },
          // Phase 4: analytics, violators, policy, reports
        ],
      },

      // === Business Portal ===
      {
        element: <RequireRole allowedRoles={['business']} />,
        children: [
          { path: '/business', element: <BusinessDashboardPage /> },
          // Phase 4: pre-check, compliance, notices
        ],
      },

      // === E-commerce Integration ===
      {
        element: <RequireRole allowedRoles={['ecommerce_partner']} />,
        children: [
          { path: '/ecommerce', element: <EcommerceDashboardPage /> },
          // Phase 4: upload, flagged
        ],
      },

      // === Rule Admin ===
      {
        element: <RequireRole allowedRoles={['rule_admin']} />,
        children: [
          { path: '/rule-admin', element: <RuleAdminDashboardPage /> },
          // Phase 4: rules, drafts, sandbox
        ],
      },
    ],
  },

  // Default redirect
  {
    path: '/',
    element: <Navigate to="/login" replace />,
  },
  {
    path: '*',
    element: <Navigate to="/login" replace />,
  },
]);
