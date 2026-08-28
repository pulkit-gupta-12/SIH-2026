/**
 * Route configuration — role-based routing with guards.
 * Each dashboard section is wrapped in a RequireRole guard.
 */
import { createBrowserRouter, Navigate } from 'react-router-dom';
import AppShell from '../components/layout/AppShell';
import RequireRole from './guards/RequireRole';
import LoginPage from '../features/auth/LoginPage';

// Citizen Pages (Phase 4.1)
import CitizenDashboardPage from '../features/citizen/pages/DashboardPage';
import ScanSearchPage from '../features/citizen/pages/ScanSearchPage';
import ComplianceSnapshotPage from '../features/citizen/pages/ComplianceSnapshotPage';
import ProductInfoPage from '../features/citizen/pages/ProductInfoPage';
import FileComplaintPage from '../features/citizen/pages/FileComplaintPage';
import ComplaintStatusPage from '../features/citizen/pages/ComplaintStatusPage';

// Field Officer Pages (Phase 4.2)
import OfficerDashboardPage from '../features/officer/pages/DashboardPage';
import InspectionQueuePage from '../features/officer/pages/InspectionQueuePage';
import GuidedCapturePage from '../features/officer/pages/GuidedCapturePage';
import ProcessingResultPage from '../features/officer/pages/ProcessingResultPage';
import ReviewFindingsPage from '../features/officer/pages/ReviewFindingsPage';
import ViolationHistoryPage from '../features/officer/pages/ViolationHistoryPage';
import CaseCreationPage from '../features/officer/pages/CaseCreationPage';

// State Controller Pages
import ControllerDashboardPage from '../features/controller/pages/DashboardPage';

// National Admin & Rule Admin Pages (Phase 4.3)
import AdminDashboardPage from '../features/admin/pages/AdminDashboardPage';
import NotificationMonitorPage from '../features/admin/pages/NotificationMonitorPage';
import DraftReviewPage from '../features/admin/pages/DraftReviewPage';
import SimulationPage from '../features/admin/pages/SimulationPage';
import PublishRulePage from '../features/admin/pages/PublishRulePage';
import RuleRepositoryPage from '../features/admin/pages/RuleRepositoryPage';

// Other Role Portals
import BusinessDashboardPage from '../features/business-portal/pages/DashboardPage';
import EcommerceDashboardPage from '../features/ecommerce-integration/pages/DashboardPage';

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
        ],
      },

      // === National Admin & Rule Admin (Phase 4.3) ===
      {
        element: <RequireRole allowedRoles={['national_admin', 'rule_admin']} />,
        children: [
          { path: '/admin', element: <AdminDashboardPage /> },
          { path: '/national', element: <AdminDashboardPage /> },
          { path: '/rule-admin', element: <AdminDashboardPage /> },
          { path: '/admin/rules', element: <RuleRepositoryPage /> },
          { path: '/admin/rules/notifications', element: <NotificationMonitorPage /> },
          { path: '/admin/rules/:id/review', element: <DraftReviewPage /> },
          { path: '/admin/rules/:id/simulate', element: <SimulationPage /> },
          { path: '/admin/rules/:id/publish', element: <PublishRulePage /> },
        ],
      },

      // === Business Portal ===
      {
        element: <RequireRole allowedRoles={['business']} />,
        children: [
          { path: '/business', element: <BusinessDashboardPage /> },
        ],
      },

      // === E-commerce Integration ===
      {
        element: <RequireRole allowedRoles={['ecommerce_partner']} />,
        children: [
          { path: '/ecommerce', element: <EcommerceDashboardPage /> },
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
