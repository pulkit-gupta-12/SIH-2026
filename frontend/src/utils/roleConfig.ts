/**
 * Role configuration — maps role IDs to display info and theme colors.
 */
import type { UserRole } from '../store/authStore';

export interface RoleConfig {
  id: UserRole;
  label: string;
  shortLabel: string;
  color: string;
  colorLight: string;
  colorDark: string;
  icon: string;
  homePath: string;
  description: string;
}

export const ROLE_CONFIGS: Record<UserRole, RoleConfig> = {
  citizen: {
    id: 'citizen',
    label: 'Citizen / Consumer',
    shortLabel: 'Citizen',
    color: 'var(--color-citizen)',
    colorLight: 'var(--color-citizen-light)',
    colorDark: 'var(--color-citizen-dark)',
    icon: '👤',
    homePath: '/citizen',
    description: 'Scan products, check compliance, file complaints',
  },
  field_officer: {
    id: 'field_officer',
    label: 'Field Officer / Inspector',
    shortLabel: 'Officer',
    color: 'var(--color-officer)',
    colorLight: 'var(--color-officer-light)',
    colorDark: 'var(--color-officer-dark)',
    icon: '🔍',
    homePath: '/officer',
    description: 'Inspect products, capture labels, create cases',
  },
  rule_admin: {
    id: 'rule_admin',
    label: 'Rule Engine Admin',
    shortLabel: 'Rule Admin',
    color: 'var(--color-ruleadmin)',
    colorLight: 'var(--color-ruleadmin-light)',
    colorDark: 'var(--color-ruleadmin-dark)',
    icon: '⚖️',
    homePath: '/admin',
    description: 'Draft, simulate, and publish compliance rules',
  },
};

export const getRoleConfig = (role: UserRole): RoleConfig => {
  return ROLE_CONFIGS[role];
};

export const ALL_ROLES: UserRole[] = [
  'citizen',
  'field_officer',
  'rule_admin',
];
