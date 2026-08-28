/**
 * Route configuration — role-based routing with guards.
 * Each dashboard section is wrapped in a RequireRole guard.
 */
import { createBrowserRouter, Navigate } from 'react-router-dom';
import AppShell from '../components/layout/AppShell';
import RequireRole from './guards/RequireRole';
import LoginPage from '../features/auth/LoginPage';

// Dashboard pages
import CitizenDashboardPage from '../features/citizen/pages/DashboardPage';
import ScanSearchPage from '../features/citizen/pages/ScanSearchPage';
import ComplianceSnapshotPage from '../features/citizen/pages/ComplianceSnapshotPage';
import ProductInfoPage from '../features/citizen/pages/ProductInfoPage';
import FileComplaintPage from '../features/citizen/pages/FileComplaintPage';
import ComplaintStatusPage from '../features/citizen/pages/ComplaintStatusPage';

import OfficerDashboardPage from '../features/officer/pages/DashboardPage';
import InspectionQueuePage from '../features/officer/pages/InspectionQueuePage';
import GuidedCapturePage from '../features/officer/pages/GuidedCapturePage';
import ProcessingResultPage from '../features/officer/pages/ProcessingResultPage';
import ReviewFindingsPage from '../features/officer/pages/ReviewFindingsPage';
import ViolationHistoryPage from '../features/officer/pages/ViolationHistoryPage';
import CaseCreationPage from '../features/officer/pages/CaseCreationPage';

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
      // === Citizen (Phase 4.1) ===
      {
        element: <RequireRole allowedRoles={['citizen']} />,
        children: [
          { path: '/citizen', element: <CitizenDashboardPage /> },
          { path: '/citizen/scan', element: <ScanSearchPage /> },
          { path: '/citizen/product/:productId/snapshot', element: <ComplianceSnapshotPage /> },
          { path: '/citizen/product/:productId', element: <ProductInfoPage /> },
          { path: '/citizen/complaint/new', element: <FileComplaintPage /> },
          { path: '/citizen/complaints', element: <ComplaintStatusPage /> },
        ],
      },

      // === Field Officer (Phase 4.2) ===
      {
        element: <RequireRole allowedRoles={['field_officer']} />,
        children: [
          { path: '/officer', element: <OfficerDashboardPage /> },
          { path: '/officer/queue', element: <InspectionQueuePage /> },
          { path: '/officer/capture', element: <GuidedCapturePage /> },
          { path: '/officer/scan/:scanId/result', element: <ProcessingResultPage /> },
          { path: '/officer/check/:checkId/review', element: <ReviewFindingsPage /> },
          { path: '/officer/product/:productId/history', element: <ViolationHistoryPage /> },
          { path: '/officer/case/new', element: <CaseCreationPage /> },
          { path: '/officer/cases', element: <CaseCreationPage /> },
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
