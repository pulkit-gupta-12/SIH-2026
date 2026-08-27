/**
 * RequireRole — route guard component.
 * Redirects to login if not authenticated.
 * Redirects to the user's own dashboard if they hit an unauthorized route.
 */
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { ROLE_CONFIGS } from '../../utils/roleConfig';
import type { UserRole } from '../../store/authStore';

interface Props {
  allowedRoles: UserRole[];
}

export default function RequireRole({ allowedRoles }: Props) {
  const { isAuthenticated, user, activeRole } = useAuthStore();

  // Not logged in → login page
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  // Check if user has any of the allowed roles
  const hasAccess = user.roles.some((r) => allowedRoles.includes(r as UserRole));

  if (!hasAccess) {
    // Redirect to user's own dashboard, not a generic 403
    const roleConfig = activeRole ? ROLE_CONFIGS[activeRole] : null;
    const redirectTo = roleConfig?.homePath || '/login';
    return <Navigate to={redirectTo} replace />;
  }

  return <Outlet />;
}
